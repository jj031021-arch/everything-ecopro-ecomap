"""
주소 -> (위도, 경도) 변환 유틸리티

우선순위:
1. Kakao 로컬 API (st.secrets['KAKAO_API_KEY']가 설정된 경우) - 한국 주소 정확도가 가장 높음
2. Nominatim (OpenStreetMap, 무료/키 불필요) - 폴백용
"""
import time
import requests
import streamlit as st


def _geocode_kakao(address: str, api_key: str):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    try:
        res = requests.get(url, headers=headers, params={"query": address}, timeout=5)
        res.raise_for_status()
        docs = res.json().get("documents", [])
        if docs:
            return float(docs[0]["y"]), float(docs[0]["x"])
    except Exception:
        pass
    return None, None


def _geocode_nominatim(address: str):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "tumbler-cafe-eco-map/1.0"}
    try:
        res = requests.get(
            url,
            headers=headers,
            params={"q": address, "format": "json", "limit": 1, "countrycodes": "kr"},
            timeout=5,
        )
        res.raise_for_status()
        results = res.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None, None


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24 * 30)
def geocode_address(address: str):
    """주소 문자열을 (lat, lon) 튜플로 변환. 실패 시 (None, None)."""
    if not address:
        return None, None

    kakao_key = st.secrets.get("KAKAO_API_KEY", None) if hasattr(st, "secrets") else None
    if kakao_key:
        lat, lon = _geocode_kakao(address, kakao_key)
        if lat is not None:
            return lat, lon

    # Nominatim 사용량 정책 준수를 위해 약간의 지연
    time.sleep(1)
    return _geocode_nominatim(address)
