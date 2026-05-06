# is-this-phishing-ai
AI-based phishing URL detection model that predicts risk levels from received SMS/text messages.

is-this-phishing-ai/
├─ app/                         # FastAPI 기반 AI 분석 서버 코드
│  ├─ main.py                   # FastAPI 앱 실행 진입점
│  ├─ api/                      # API 라우터 관리 폴더
│  │  └─ analyze.py             # 문자/URL 분석 요청을 처리하는 /analyze API
│  ├─ services/                 # 실제 분석 로직을 담당하는 서비스 코드
│  │  ├─ url_analyzer.py        # URL 구조 분석: HTTPS, 도메인, 길이, 의심 TLD 등
│  │  ├─ pattern_analyzer.py    # 행동유도 패턴 분석: 긴급성, 공포, 보상, 개인정보 유도 등
│  │  └─ risk_scorer.py         # 각 분석 점수를 통합해 최종 위험도 산출
│  ├─ models/                   # 요청/응답 데이터 형식 정의
│  │  └─ schemas.py             # Pydantic 기반 Request/Response Schema
│  └─ ml/                       # 머신러닝/딥러닝 모델 연동 코드
│     └─ phishing_model.py      # 학습된 피싱 탐지 모델 로드 및 예측 함수
│
├─ data/                        # 데이터셋 저장 폴더
│  ├─ raw/                      # 원본 피싱/정상 문자 및 URL 데이터
│  └─ processed/                # 전처리 완료된 학습용 데이터
│
├─ notebooks/                   # 모델 실험 및 학습용 Jupyter/Colab 노트북
│  └─ model_experiment.ipynb    # 모델 학습, 성능 비교, 실험 기록
│
├─ saved_models/                # 학습 완료된 모델 파일 저장 폴더
├─ tests/                       # 기능 테스트 및 API 테스트 코드
│
├─ requirements.txt             # 프로젝트 실행에 필요한 Python 패키지 목록
├─ README.md                    # 프로젝트 설명 문서
├─ .gitignore                   # Git에 올리지 않을 파일/폴더 설정
└─ LICENSE                      # 오픈소스 라이선스
