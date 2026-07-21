import os
from datetime import datetime

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from utils.geocoding import geocode_address
from utils.github_sync import commit_file, is_configured as github_configured

# ------------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------------
st.set_page_config(page_title="에브리띵 에코 맵", page_icon="🌱", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CAFES_PATH = os.path.join(DATA_DIR, "cafes.csv")
REVIEWS_PATH = os.path.join(DATA_DIR, "reviews.csv")

SEOUL_CENTER = [37.5665, 126.9780]


# ------------------------------------------------------------------
# 데이터 로드 / 저장
# ------------------------------------------------------------------
def load_cafes() -> pd.DataFrame:
    df = pd.read_csv(CAFES_PATH, dtype={"id": "Int64"})
    for col in ["lat", "lon"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_reviews() -> pd.DataFrame:
    return pd.read_csv(REVIEWS_PATH, dtype={"cafe_id": "Int64"})


def save_cafes(df: pd.DataFrame):
    df.to_csv(CAFES_PATH, index=False)
    if github_configured():
        commit_file("data/cafes.csv", df.to_csv(index=False), "카페 데이터 업데이트")


def save_reviews(df: pd.DataFrame):
    df.to_csv(REVIEWS_PATH, index=False)
    if github_configured():
        commit_file("data/reviews.csv", df.to_csv(index=False), "후기 데이터 업데이트")


def next_id(df: pd.DataFrame) -> int:
    if df.empty:
        return 1
    return int(df["id"].max()) + 1


# ------------------------------------------------------------------
# 세션 상태 초기화
# ------------------------------------------------------------------
if "cafes_df" not in st.session_state:
    st.session_state.cafes_df = load_cafes()
if "reviews_df" not in st.session_state:
    st.session_state.reviews_df = load_reviews()
if "selected_cafe_id" not in st.session_state:
    st.session_state.selected_cafe_id = None


# ------------------------------------------------------------------
# 좌표 없는 카페 자동 지오코딩 (최초 1회, 결과는 캐시/저장됨)
# ------------------------------------------------------------------
def geocode_missing():
    df = st.session_state.cafes_df
    missing = df[df["lat"].isna() | df["lon"].isna()]
    if missing.empty:
        return

    progress = st.progress(0.0, text=f"주소 좌표 변환 중... (0/{len(missing)})")
    updated = False
    for n, (idx, row) in enumerate(missing.iterrows(), start=1):
        lat, lon = geocode_address(row["address"])
        if lat is not None:
            df.at[idx, "lat"] = lat
            df.at[idx, "lon"] = lon
            updated = True
        progress.progress(n / len(missing), text=f"주소 좌표 변환 중... ({n}/{len(missing)})")
    progress.empty()

    if updated:
        st.session_state.cafes_df = df
        save_cafes(df)


geocode_missing()

df = st.session_state.cafes_df
reviews_df = st.session_state.reviews_df
plottable = df.dropna(subset=["lat", "lon"])


# ------------------------------------------------------------------
# 헤더
# ------------------------------------------------------------------
st.title("🌱 에브리띵 에코 맵")
st.caption("텀블러를 가져가면 할인해주는 카페들을 지도에서 찾아보고, 직접 카페를 추가하거나 후기를 남겨보세요.")

col_stat1, col_stat2, col_stat3 = st.columns(3)
col_stat1.metric("등록된 카페 수", f"{len(df)}곳")
col_stat2.metric("지도에 표시된 카페", f"{len(plottable)}곳")
col_stat3.metric("등록된 후기 수", f"{len(reviews_df)}개")

if len(plottable) < len(df):
    st.info(f"좌표를 찾지 못한 카페가 {len(df) - len(plottable)}곳 있어 지도에 표시되지 않았어요. 주소를 다시 확인해주세요.")

st.divider()


# ------------------------------------------------------------------
# 지도
# ------------------------------------------------------------------
map_col, detail_col = st.columns([2, 1])

with map_col:
    m = folium.Map(location=SEOUL_CENTER, zoom_start=11, tiles="CartoDB positron")

    for _, row in plottable.iterrows():
        popup_html = f"""
        <div style='font-size:14px; min-width:180px'>
            <b>{row['name']}</b><br>
            <span style='color:#2e7d32;'>☕ {row['discount'] if pd.notna(row['discount']) and row['discount'] else '할인 정보 없음'}</span><br>
            <span style='color:#555;'>📍 {row['address']}</span>
        </div>
        """
        folium.Marker(
            location=[row["lat"], row["lon"]],
            tooltip=row["name"],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color="green", icon="cutlery", prefix="fa"),
        ).add_to(m)

    map_result = st_folium(m, height=560, width=None, returned_objects=["last_object_clicked"])

# 클릭된 마커와 가장 가까운 카페 매칭
if map_result and map_result.get("last_object_clicked"):
    click = map_result["last_object_clicked"]
    clat, clon = click.get("lat"), click.get("lng")
    if clat is not None and clon is not None:
        plottable = plottable.copy()
        plottable["_dist"] = (plottable["lat"] - clat) ** 2 + (plottable["lon"] - clon) ** 2
        nearest = plottable.sort_values("_dist").iloc[0]
        st.session_state.selected_cafe_id = int(nearest["id"])


# ------------------------------------------------------------------
# 상세 정보 + 후기
# ------------------------------------------------------------------
with detail_col:
    st.subheader("📌 상세 정보")

    if st.session_state.selected_cafe_id is None:
        st.write("지도에서 카페 아이콘을 클릭하면 할인 정보와 주소, 후기가 여기에 표시돼요.")
    else:
        cafe_row = df[df["id"] == st.session_state.selected_cafe_id]
        if cafe_row.empty:
            st.write("선택한 카페 정보를 찾을 수 없어요.")
        else:
            cafe = cafe_row.iloc[0]
            st.markdown(f"### {cafe['name']}")
            st.markdown(f"**☕ 할인 정보:** {cafe['discount'] if pd.notna(cafe['discount']) and cafe['discount'] else '정보 없음'}")
            st.markdown(f"**📍 주소:** {cafe['address']}")
            if pd.notna(cafe.get("note")) and cafe.get("note"):
                st.markdown(f"**📝 비고:** {cafe['note']}")

            st.markdown("---")
            st.markdown("#### 💬 후기")

            cafe_reviews = reviews_df[reviews_df["cafe_id"] == cafe["id"]].sort_values(
                "timestamp", ascending=False
            )
            if cafe_reviews.empty:
                st.caption("아직 등록된 후기가 없어요. 첫 후기를 남겨보세요!")
            else:
                for _, rv in cafe_reviews.iterrows():
                    stars = "⭐" * int(rv["rating"]) if pd.notna(rv["rating"]) else ""
                    author = rv["author"] if pd.notna(rv["author"]) and rv["author"] else "익명"
                    st.markdown(f"**{author}** {stars}")
                    st.caption(f"{rv['comment']}  \n_{rv['timestamp']}_")
                    st.markdown("---")

            with st.form(key=f"review_form_{cafe['id']}", clear_on_submit=True):
                r_author = st.text_input("닉네임 (선택)")
                r_rating = st.slider("평점", 1, 5, 5)
                r_comment = st.text_area("후기 내용", placeholder="이 카페에서의 경험을 남겨주세요.")
                submitted = st.form_submit_button("후기 등록")

                if submitted:
                    if not r_comment.strip():
                        st.warning("후기 내용을 입력해주세요.")
                    else:
                        new_review = pd.DataFrame([{
                            "cafe_id": cafe["id"],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "author": r_author.strip() or "익명",
                            "rating": r_rating,
                            "comment": r_comment.strip(),
                        }])
                        st.session_state.reviews_df = pd.concat(
                            [st.session_state.reviews_df, new_review], ignore_index=True
                        )
                        save_reviews(st.session_state.reviews_df)
                        st.success("후기가 등록되었어요!")
                        st.rerun()


st.divider()

# ------------------------------------------------------------------
# 새 카페 추가
# ------------------------------------------------------------------
with st.expander("➕ 새로운 텀블러 할인 카페 추가하기"):
    with st.form("add_cafe_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        new_name = c1.text_input("카페 이름 *")
        new_discount = c2.text_input("할인 내용 *", placeholder="예: 텀블러 300원 할인")
        new_address = st.text_input("주소 (도로명 주소) *", placeholder="예: 서울 용산구 청파로47길 78")
        new_note = st.text_input("비고 (선택)")
        add_submitted = st.form_submit_button("카페 추가")

        if add_submitted:
            if not new_name.strip() or not new_address.strip() or not new_discount.strip():
                st.warning("이름, 주소, 할인 내용은 필수 입력이에요.")
            else:
                with st.spinner("주소를 좌표로 변환하는 중..."):
                    lat, lon = geocode_address(new_address.strip())

                if lat is None:
                    st.error("주소로 좌표를 찾지 못했어요. 도로명 주소를 다시 확인해주세요.")
                else:
                    new_row = pd.DataFrame([{
                        "id": next_id(st.session_state.cafes_df),
                        "name": new_name.strip(),
                        "address": new_address.strip(),
                        "lat": lat,
                        "lon": lon,
                        "discount": new_discount.strip(),
                        "note": new_note.strip(),
                        "source": "user_added",
                    }])
                    st.session_state.cafes_df = pd.concat(
                        [st.session_state.cafes_df, new_row], ignore_index=True
                    )
                    save_cafes(st.session_state.cafes_df)
                    st.success(f"'{new_name.strip()}' 카페가 추가되었어요!")
                    st.rerun()

if not github_configured():
    st.caption(
        "ℹ️ 현재 GitHub 저장소 연동이 설정되어 있지 않아, 새로 추가한 카페/후기는 이 세션(브라우저 새로고침 전까지)에만 저장돼요. "
        "영구 저장을 원한다면 README.md의 안내를 따라 GitHub 연동을 설정해주세요."
    )
