# is-this-phishing-ai
AI-based phishing URL detection model that predicts risk levels from received SMS/text messages.

## Project Structure

```text
is-this-phishing-ai/
├─ app/                         # FastAPI 기반 AI 분석 서버 코드
│  ├─ main.py                   # FastAPI 앱 실행 진입점
│  ├─ api/                      # API 라우터 관리 폴더
│  │  └─ analyze.py             # 문자/URL 분석 요청 처리 API
│  ├─ services/                 # 실제 분석 로직
│  │  ├─ url_analyzer.py        # URL 구조 분석
│  │  ├─ pattern_analyzer.py    # 행동유도 패턴 분석
│  │  └─ risk_scorer.py         # 최종 위험도 계산
│  ├─ models/                   # Request/Response Schema
│  │  └─ schemas.py
│  └─ ml/                       # 머신러닝 모델 연동
│     └─ phishing_model.py (이거 아직 안만듬 - 코랩 실험 파일 만들고 올리면 됨)
│
├─ data/                        # 데이터셋 저장 폴더
│  ├─ raw/                      # 원본 데이터
│  └─ processed/                # 전처리 데이터
│
├─ notebooks/                   # 모델 실험용 노트북
│  └─ model_experiment.ipynb
│
├─ saved_models/                # 학습된 모델 저장 폴더
├─ tests/                       # 테스트 코드
│
├─ requirements.txt             # Python 패키지 목록
├─ README.md                    # 프로젝트 설명 문서
├─ .gitignore                   # Git 제외 설정
└─ LICENSE                      # 오픈소스 라이선스
```
