# 🌱 에브리띵 에코 맵

텀블러 할인이 되는 카페들을 지도에서 찾아보는 Streamlit 대시보드입니다.

- 지도에서 카페 아이콘을 클릭하면 **할인 정보 + 주소**가 표시돼요
- 카페를 선택한 상태에서 **후기를 작성**할 수 있어요
- 누구나 **새로운 카페를 직접 추가**할 수 있어요

---

## 1. 로컬에서 실행해보기

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 로 접속하면 됩니다.

이 상태로는 지오코딩(주소→좌표 변환)은 무료 Nominatim으로 동작하고, 새로 추가한 카페/후기는
**세션이 끝나면(=streamlit 재시작하면) 로컬 data/*.csv 파일에 저장된 그대로 유지**됩니다. (로컬 실행은 파일시스템이 유지되므로 문제 없어요)

---

## 2. GitHub에 올리기

1. GitHub에서 새 저장소를 만듭니다. (예: `tumbler-cafe-eco-map`)
2. 이 폴더 전체를 그 저장소에 push 합니다.

```bash
git init
git add .
git commit -m "init: 에브리띵 에코 맵"
git branch -M main
git remote add origin https://github.com/{내-아이디}/{저장소이름}.git
git push -u origin main
```

> ⚠️ `.streamlit/secrets.toml` 파일은 `.gitignore`에 의해 자동으로 제외됩니다. 절대 API 키를 커밋하지 마세요.

---

## 3. Streamlit Community Cloud로 배포하기

1. https://share.streamlit.io 접속 후 GitHub 계정으로 로그인
2. "New app" → 방금 만든 저장소 / `main` 브랜치 / `app.py` 선택 → Deploy
3. 배포된 앱의 **Settings → Secrets** 메뉴에서 아래 내용을 붙여넣기 (`.streamlit/secrets.toml.example` 참고)

```toml
KAKAO_API_KEY = "카카오에서_발급받은_REST_API_키"

GITHUB_TOKEN = "저장소_쓰기권한_있는_PAT"
GITHUB_REPO = "내아이디/저장소이름"
GITHUB_BRANCH = "main"
```

### 왜 GitHub 토큰이 필요한가요?
Streamlit Community Cloud는 앱이 재시작/재배포될 때마다 파일시스템이 초기화돼요.
그래서 사용자가 추가한 카페나 후기가 사라지지 않게 하려면, 앱이 변경사항을 **GitHub 저장소에 직접 커밋**해서
`data/cafes.csv`, `data/reviews.csv` 파일 자체를 갱신하도록 만들었습니다.

- GITHUB_TOKEN을 설정하지 않아도 앱은 정상 동작하지만, 새로 추가한 데이터는 **그 세션 동안만** 유지돼요.
- 토큰을 설정하면, 추가/후기 작성 즉시 저장소에 커밋되어 **누가 언제 다시 접속해도 유지**됩니다.

**GitHub 토큰 발급 방법**
1. https://github.com/settings/tokens → "Generate new token (classic)" 또는 fine-grained token
2. 저장소에 대한 `Contents: Read and write` 권한 부여
3. 생성된 토큰 값을 `GITHUB_TOKEN`에 입력

### 왜 카카오 API 키가 필요한가요? (선택)
한국 도로명 주소는 카카오 로컬 API가 Nominatim보다 정확도가 높아요. 키가 없으면 자동으로 무료
Nominatim(OpenStreetMap)으로 대체되므로 필수는 아닙니다.

**카카오 API 키 발급 방법**
1. https://developers.kakao.com → 애플리케이션 추가
2. "앱 키" 중 **REST API 키** 복사 → `KAKAO_API_KEY`에 입력

---

## 4. 폴더 구조

```
cafe-eco-map/
├── app.py                     # 메인 Streamlit 앱
├── requirements.txt
├── .streamlit/
│   └── secrets.toml.example   # secrets.toml 작성용 예시 (실제 파일은 .gitignore 처리)
├── utils/
│   ├── geocoding.py           # 주소 → 좌표 변환 (카카오 / Nominatim)
│   └── github_sync.py         # GitHub Contents API로 CSV 커밋
└── data/
    ├── cafes.csv              # 카페 목록 (이름/주소/좌표/할인/출처)
    └── reviews.csv            # 카페별 후기
```

## 5. 데이터 직접 수정하고 싶다면
`data/cafes.csv`를 엑셀/스프레드시트로 열어 직접 행을 추가/수정한 뒤 GitHub에 push해도 됩니다.
`lat`, `lon` 칸을 비워두면 앱 실행 시 자동으로 좌표를 채워줍니다.
