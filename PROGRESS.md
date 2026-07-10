# PhishGuard 개발 진행 상황

개발가이드(파트별 개발 가이드) 기준 A/B/C 트랙 전체 체크리스트입니다.
완료된 항목은 `[x]`로 표시되어 있으며, 각자 작업하면서 체크박스를 업데이트해주세요.

---

## Phase 0 — 공통 0일차 (다 같이, 30분)

- [ ] 스켈레톤 클론 → `pip install -r requirements.txt`
- [ ] `uvicorn app.main:app --reload` 실행 → `http://localhost:8000/docs` 확인
- [ ] `INTEGRATION.md` ①~⑦ 같이 읽고 합의, 체크리스트 체크
- [ ] GitHub 브랜치 파기: `feat/model-a`, `feat/backend-b`, `feat/front-c`
- [ ] `.env` 만들고 `.gitignore`에 추가 → `git ls-files | grep .env` 아무것도 안 나오는지 확인

---

## Phase 1 — A 트랙: 모델 · 데이터 · 평가

- [ ] **A1.** 데이터 확보 + 라이선스 확인 — `data/raw.csv` 확보, 라이선스 상태 기록
- [ ] **A2.** 데이터 탐색 (class 값 정체 파악) — 라벨 매핑 규칙 확정, 팀 공유 (계약 ⑥)
- [ ] **A3.** 전처리 스크립트 — `scripts/prepare_data.py` (신규), `data/train.parquet`/`val.parquet` 생성
- [ ] **A4.** 베이스라인 — `scripts/baseline.py`, TF-IDF+LogReg F1 기록
- [ ] **A5.** KcELECTRA 파인튜닝 — `scripts/train_text.py`, `models/text_clf/` 생성
- [ ] **A6.** 통합 확인 — `uvicorn` 재시작 후 `[classifier] KcELECTRA 로드됨` 로그 확인
- [ ] **A7.** 합성 증강 (지속, W1~W2) — `scripts/augment.py`, 학습셋 v2
- [ ] **A8.** 시간분할 테스트셋 — `data/test_recent.parquet`
- [ ] **A9.** 융합 메타분류기 — `scripts/train_fusion.py`, `models/fusion.pkl`
- [ ] **A10.** 평가 — `scripts/evaluate.py`, 발표용 성능 표·그래프 완성

---

## Phase 2 — B 트랙: 백엔드 · 인텔리전스

- [ ] **B1.** 규칙엔진 실데이터 연결 — `rules.py`, `seed/phishing_urls.txt`, 도메인 나이(whois) 반영
- [ ] **B2.** 평판DB 시드 확대 — `seed/reports.json`, `/api/graph`에서 클러스터 여러 개 형성
- [ ] **B3.** 그래프 정교화 — `graph.py`, 클러스터 위험도 계산 개선, `to_json` 형식(계약②) 확인
- [ ] **B4.** 설명 경로 Claude 연결 — `explain.py`, `.env`에 `ANTHROPIC_API_KEY` 설정
- [ ] **B5.** (선택) RAG 유사사례 — `explain.py`의 `retrieve_similar`
- [ ] **B6.** 신고 + 트렌드 엔드포인트 — `main.py`, `/api/report` 확인 + `/api/trends` 추가
- [ ] **B7.** A 모델 통합 확인 — `models/text_clf/`, `fusion.pkl` 반영 후 재시작만으로 동작
- [ ] **B8.** 적대적 강건성 데모 경로 — 난독화 문자 탐지 데모 세트

### 신고 기능(Report) — B 담당 세부 항목
- [ ] `POST /api/report` 동작 확인 (신고 시 DB 저장 + 그래프 갱신)
- [ ] `AnalyzeResponse`에 `urls: list[str]` 필드 추가
- [ ] `analyze.py`에서 `urls=pre["urls"]` 채워서 응답에 포함
- [ ] C에게 "urls 필드 추가함" 공지 (INTEGRATION 계약 ① 갱신)
- [ ] (선택) `reputation.py`에 pending 테이블 추가 — 후보/확정 분리

---

## Phase 3 — C 트랙: 프론트 · 데모

- [x] **C1.** Vite React 세팅 — `frontend/`, `/api → localhost:8000` 프록시
- [x] **C2.** API 클라이언트 — `src/api/client.js` (계약 ①②③) + `src/api/normalize.js`
- [x] **C3.** 입력 화면 — `src/pages/Analyze.jsx`
- [x] **C4.** 결과 화면 — `src/components/Result.jsx`
- [x] **C5.** 그래프 시각화 — `src/components/OrgGraph.jsx`, `src/pages/Graph.jsx`
- [x] **C6.** 신고 버튼 → 신고 페이지 — `src/pages/Report.jsx`
- [x] **C7.** 트렌드 대시보드 — `src/pages/Trends.jsx`
- [ ] **C8.** 데모 시나리오 + 발표덱 — 골든패스 스크립트화, 덱, 리허설, 녹화 백업

### 신고 기능(Report) — C 담당 세부 항목
- [x] 신고 문구 자동생성 함수 `buildReportText()`
- [x] 신고 섹션 UI: 문구 미리보기(textarea) + 버튼
- [x] 버튼 동작: PhishGuard DB 신고 / 복사+공식사이트 이동
- [x] 결과 화면에 [신고하기] → 신고 섹션 연결
- [ ] ⚠️ **미확정**: 신고 제출 후 화면 전환 방식 — 가이드 PDF는 "이동 없음", 유저플로우 문서는 "그래프 화면 이동"을 요구. 현재는 유저플로우 문서 기준으로 구현됨 (`Report.jsx`의 `navigate('/graph', ...)` 한 줄만 고치면 변경 가능)

### C 트랙 추가 작업 (가이드에는 없지만 진행된 것)
- [x] 라이트 테마 UI 전면 적용 (blue/cyan 브랜드 컬러)
- [x] 커스텀 로고(`Logo.jsx`) 제작
- [x] 시작 스플래시 애니메이션
- [x] 홈 랜딩 화면 + 하단 4탭 내비게이션(홈/분석/그래프/트렌드)
- [x] "최근 분석 결과" 로컬 히스토리 (localStorage)
- [x] 와이어프레임 디자인 파일 기준 레이아웃 반영 (스탯 타일, 순위 배지, 로딩/에러 상태 등)

---

## 트랙 간 동기화 메모

| 이 작업 | 필요조건 | 그전엔 이걸로 |
|---|---|---|
| C4 결과화면 | 없음 (스켈레톤 폴백이 응답 줌) | 바로 시작 가능 |
| C5 그래프 | 없음 (시드로 그래프 나옴) | 바로 시작 가능 |
| B7 모델통합 | A6 (모델 저장) | 폴백으로 개발 |
| A9 융합학습 | B1~B2 (신호 추출 가능) | 가중합으로 개발 |
| A10 평가 | A9 + B 신호 완성 | — |

**핵심 원칙**: 아무도 남을 안 기다림. 스켈레톤이 전부 폴백으로 응답을 주니까, A가 학습하는 동안 B·C는 실제 데이터 없이도 자기 화면·로직을 완성한다. 실모델은 인터페이스 뒤에서 조용히 교체될 뿐.

**관통 마일스톤**: W1 말까지 세 트랙을 붙여서 "문자 붙여넣기 → 위험도+근거+그래프 → 신고 → 그래프 갱신"이 스텁으로라도 한 번 끝까지 돌아가게. (C 트랙은 이 마일스톤 기준으로는 완료 상태)
