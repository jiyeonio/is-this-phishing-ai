"""루트 공통 설정 (계약 ⑦ 환경 계약).

전원이 공유하는 값. A/B/C 아무나 함부로 못 바꿈 — 바꾸려면 관련자 합의.
지금은 최소 폴백 기본값. 실제 값은 .env / 환경변수로 덮어씀.
"""

import os

# --- 포트 ---------------------------------------------------------------
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5173"))

# --- CORS ---------------------------------------------------------------
# 프론트(Vite) 오리진만 허용. 안 맞으면 브라우저 호출이 CORS로 막힘.
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    f"http://localhost:{FRONTEND_PORT},http://127.0.0.1:{FRONTEND_PORT}",
).split(",")

# --- 위험도 임계값 (계약 ⑦) --------------------------------------------
# level 판정: score >= DANGER → danger, >= SUSPICIOUS → suspicious, 그 외 safe
THRESHOLD_SUSPICIOUS = float(os.getenv("THRESHOLD_SUSPICIOUS", "0.40"))
THRESHOLD_DANGER = float(os.getenv("THRESHOLD_DANGER", "0.70"))

# --- 모델 경로 (A 저장 = B 로드, 같은 값) -------------------------------
TEXT_CLF_PATH = os.getenv("TEXT_CLF_PATH", "models/text_clf/")
FUSION_MODEL_PATH = os.getenv("FUSION_MODEL_PATH", "models/fusion.pkl")

# --- API 키 (.env에 두고 git 추적 금지) ---------------------------------
# 없으면 explain.py가 템플릿 폴백으로 동작 (데모 안전).
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --- 시드 데이터 경로 ---------------------------------------------------
SEED_DIR = os.getenv("SEED_DIR", "backend/seed")
PHISHING_URLS_PATH = os.getenv(
    "PHISHING_URLS_PATH", os.path.join(SEED_DIR, "phishing_urls.txt")
)
REPORTS_SEED_PATH = os.getenv(
    "REPORTS_SEED_PATH", os.path.join(SEED_DIR, "reports.json")
)

# --- 평판 DB (SQLite, 로컬 생성 — .gitignore로 추적 제외) ---------------
REPUTATION_DB_PATH = os.getenv("REPUTATION_DB_PATH", "backend/reputation.db")
