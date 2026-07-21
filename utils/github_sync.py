"""
GitHub Contents API를 이용해 data/*.csv 변경사항을 저장소에 직접 커밋합니다.
Streamlit Community Cloud는 재배포/재시작 시 파일시스템이 초기화되므로,
사용자가 추가한 카페/후기를 영구 보존하려면 GitHub에 커밋하는 방식을 사용합니다.

필요한 st.secrets 값:
- GITHUB_TOKEN   : repo 쓰기 권한이 있는 Personal Access Token
- GITHUB_REPO    : "owner/repo" 형식
- GITHUB_BRANCH  : (선택) 기본값 "main"

토큰이 설정되어 있지 않으면 이 모듈의 함수들은 아무 동작도 하지 않고
False를 반환합니다. 이 경우 앱은 로컬(세션 중) CSV에만 저장합니다.
"""
import base64
import requests
import streamlit as st


def is_configured() -> bool:
    if not hasattr(st, "secrets"):
        return False
    return bool(st.secrets.get("GITHUB_TOKEN")) and bool(st.secrets.get("GITHUB_REPO"))


def commit_file(path: str, content_str: str, message: str) -> bool:
    """레포지토리 내 path 파일을 content_str로 덮어쓰는 커밋을 생성합니다."""
    if not is_configured():
        return False

    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    branch = st.secrets.get("GITHUB_BRANCH", "main")

    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    # 기존 파일의 sha가 필요 (업데이트인 경우)
    sha = None
    try:
        res = requests.get(api_url, headers=headers, params={"ref": branch}, timeout=10)
        if res.status_code == 200:
            sha = res.json().get("sha")
    except Exception:
        pass

    payload = {
        "message": message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    try:
        res = requests.put(api_url, headers=headers, json=payload, timeout=10)
        return res.status_code in (200, 201)
    except Exception:
        return False
