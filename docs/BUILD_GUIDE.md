# 파트별 개발 가이드

> 각자 자기 트랙을 **위에서 아래 순서대로** 진행.
각 스텝 = 목표 / 건드리는 파일 / 방법 / 완료 기준(✅).
인터페이스(함수 시그니처·API)는 `INTEGRATION.md` 계약을 절대 안 바꿈.
> 

---

## 공통 0일차 (다 같이, 30분)

1. 스켈레톤 클론 → `pip install -r requirements.txt`
2. `uvicorn app.main:app --reload` 실행 → http://localhost:8000/docs 뜨는지 확인
3. `INTEGRATION.md` ①~⑦ 같이 읽고 합의, 체크리스트 체크
4. GitHub 브랜치 파기: `feat/model-a`, `feat/backend-b`, `feat/front-c`
5. `.env` 만들고 `.gitignore`에 추가 → `git ls-files | grep .env` 아무것도 안 나오는지 확인

✅ 세 명 모두 스켈레톤이 로컬에서 돌고, 계약 합의 끝.

---

# A 트랙 — 모델 · 데이터 · 평가

### A1. 데이터 확보 + 라이선스 확인

- **목표**: meal-bbang csv 확보, 라이선스 상태 기록
- **방법**:
    
    ```python
    from datasets import load_datasetds = load_dataset("meal-bbang/Korean_message")ds["train"].to_pandas().to_csv("data/raw.csv", index=False)
    ```
    
    - HuggingFace "Files and versions"에서 LICENSE 확인 → 없으면 실험용으로만, 발표엔 출처 명시
- ✅ `data/raw.csv` 확보 + 라이선스 상태 한 줄 메모

### A2. 데이터 탐색 (class 값 정체 파악)

- **목표**: `class` 컬럼 1/2/3이 각각 뭔지, 정상/피싱 비율 확인
- **방법**: `df['class'].value_counts()` + 각 class 샘플 10개씩 눈으로 확인
- ✅ 라벨 매핑 규칙 확정 (예: 1→정상, 2→피싱, 3→처리방침). **팀에 공유** (계약 ⑥)
- 최종 라벨링
class 1 → 0 (정상)
class 2 → 1 (피싱)
class 3 → 0 (정상)

### A3. 전처리 스크립트 — `scripts/prepare_data.py` (신규)

- **목표**: raw → 학습셋. **반드시 `app.preprocess`의 함수 재사용** (학습·서빙 전처리 일치)
- **방법**:
    
    ```python
    import pandas as pd
      from app.preprocess import mask_urls, normalize
    
      df = pd.read_csv("data/raw.csv")
      df["label"] = df["class"].map({1: 0, 2: 1})   # A2에서 정한 규칙
      df = df.dropna(subset=["label"])
      df["text"] = df["content"].map(lambda t: mask_urls(normalize(str(t))))  # 서빙과 동일 마스킹
      df = df.drop_duplicates(subset=["text"])       # 중복 제거 (raw는 템플릿 반복 심함)
      # 클래스 균형 샘플링 (다수 클래스 다운샘플)
      n = df["label"].value_counts().min()
      df = df.groupby("label").sample(n=n, random_state=42)
      train = df.sample(frac=0.85, random_state=42)
      val = df.drop(train.index)
      train.to_parquet("data/train.parquet"); val.to_parquet("data/val.parquet")
      print(len(train), len(val), df["label"].value_counts().to_dict())..
    ```
    
- ✅ `data/train.parquet`, `val.parquet` 생성. 중복 제거 후 실질 개수 확인 (클래스당 3천+ 목표)

### A4. 베이스라인 (기준 수치 확보) — `scripts/baseline.py`

- **목표**: TF-IDF+LogReg로 "이만큼은 나온다" 기준선. 나중에 KcELECTRA와 비교용
- **방법**: `TfidfVectorizer(analyzer="char_wb", ngram_range=(2,4))` + `LogisticRegression`, val에서 F1 기록
- ✅ 베이스라인 F1 기록 (예: 0.9x). 발표 ablation의 비교 대상

### A5. KcELECTRA 파인튜닝 — `scripts/train_text.py`

- **목표**: 본 문자모델 학습
- **방법**:
    
    ```python
    from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                                TrainingArguments, Trainer)
      from datasets import Dataset
      import pandas as pd, numpy as np, evaluate
    
      M = "beomi/KcELECTRA-base"
      tok = AutoTokenizer.from_pretrained(M)
      model = AutoModelForSequenceClassification.from_pretrained(M, num_labels=2)
    
      def load(p):
          d = Dataset.from_pandas(pd.read_parquet(p)[["text","label"]])
          return d.map(lambda b: tok(b["text"], truncation=True, max_length=192,
                                     padding="max_length"), batched=True)
      tr, va = load("data/train.parquet"), load("data/val.parquet")
    
      f1 = evaluate.load("f1")
      args = TrainingArguments("ckpt", num_train_epochs=4, learning_rate=2e-5,
          per_device_train_batch_size=16, eval_strategy="epoch",
          load_best_model_at_end=True, metric_for_best_model="f1")
      Trainer(model, args, train_dataset=tr, eval_dataset=va,
              compute_metrics=lambda p: f1.compute(
                  predictions=np.argmax(p.predictions,1), references=p.label_ids)).train()
    
      model.save_pretrained("models/text_clf"); tok.save_pretrained("models/text_clf")
    ```
    
    - `screen` 안에서 돌리기 (서버 규칙). GPU면 몇 분~십몇 분
- ✅ `models/text_clf/` 생성 → **`classifier.py`가 자동 로드** (B가 아무것도 안 해도 됨)

### A6. 통합 확인

- **방법**: `uvicorn` 재시작 → 로그에 `[classifier] KcELECTRA 로드됨` 뜨는지, "엄마 폰 고장" 문자가 이제 높게 나오는지
- ✅ 실모델이 API에 반영됨

### A7. 합성 증강 (지속, W1~W2) — `scripts/augment.py`

- **목표**: 최신 수법(악성앱 유도 등) + 난독화(자모분리·homoglyph) 생성해 학습셋 다양성↑
- **방법**: Claude API로 유형별 신규 문장 생성 + 규칙 변형. train에 20~30% 추가
- ✅ 증강분 포함 학습셋 v2, 재학습

### A8. 시간분할 테스트셋 — `data/test_recent.parquet`

- **목표**: "신규 대응력" 증명용. 2025~26 신종 수법으로만 구성 (학습에 안 씀)
- ✅ 최신 테스트셋 확보

### A9. 융합 메타분류기 — `scripts/train_fusion.py`

- **목표**: 세 신호 → 최종 위험도 학습 (계약 ⑤ `fuse` 그대로)
- **방법**: 학습셋 각 샘플에서 `[model_p, rule_s, rep_s]` 뽑아 `fusion.train_meta(X, y)` → `models/fusion.pkl`
    - (B의 `rules.analyze`, `reputation.lookup`를 호출해서 신호 추출)
- ✅ `fusion.pkl` 생성 → `fusion.py`가 자동 사용

### A10. 평가 — `scripts/evaluate.py` (발표 핵심)

- **목표**: 표·그래프 산출
- **항목**:
    - 시간분할: `data/val`(과거) vs `data/test_recent`(최신) F1 비교 → "베이스라인 급락 vs 하이브리드 유지"
    - ablation: 모델만 / 규칙만 / 평판만 / 전체 4가지
    - 적대적: 난독화 테스트셋 F1
    - 임계값: PR커브 → 재현율 우선 지점 → `config.THRESHOLD_*` 확정
- ✅ 발표용 성능 표·그래프 완성

---

# B 트랙 — 백엔드 · 인텔리전스

### B1. 규칙엔진 실데이터 연결 — `rules.py`, `seed/phishing_urls.txt`

- **목표**: 명단을 실제 피싱 URL로 교체 + 도메인 나이 추가
- **방법**:
    - `seed/phishing_urls.txt`를 너희 URL 데이터셋으로 교체 (한 줄에 하나)
    - `python-whois`로 도메인 나이:
        
        ```python
        import whois, datetime
            def domain_age_days(dom):
                try:
                    c = whois.whois(dom).creation_date
                    c = c[0] if isinstance(c, list) else c
                    return (datetime.datetime.now() - c).days
                except Exception: return None
            # analyze() 안: age가 30 미만이면 evidence 추가 + score += 0.2
        ```
        
- ✅ 실제 피싱 URL이 조회되고, 신규 도메인이 잡힘

### B2. 평판DB 시드 확대 — `seed/reports.json`

- **목표**: 공개 사례(KISA·경찰 사칭번호 등)로 시드 확대, 조직별로 URL·문구 공유되게 구성
- ✅ `/api/graph`에서 클러스터가 여러 개 형성됨

### B3. 그래프 정교화 — `graph.py`

- **목표**: 클러스터 위험도 계산 개선, `to_json` 출력 검증
- **방법**: 커뮤니티별 신고 수·URL 수로 risk 산출식 조정. C와 `to_json` 형식(계약 ②) 확인
- ✅ 그래프 JSON이 C 라이브러리에 바로 들어감

### B4. 설명 경로 Claude 연결 — `explain.py`, `.env`

- **목표**: 템플릿 폴백 → 실제 Claude 근거 생성 (코드는 이미 있음, 키만)
- **방법**: `.env`에 `ANTHROPIC_API_KEY=...` → 자동으로 Claude 사용. 프롬프트 톤 튜닝
- ✅ 근거가 자연어 문단으로 나옴. 키 빼도 폴백으로 데모 가능(안전)

### B5. (선택) RAG 유사사례 — `explain.py` `retrieve_similar`

- **목표**: 과거 유사 피싱 사례 검색해 설명 근거 강화
- **방법**: `sentence-transformers`(ko-sroberta) 임베딩 → FAISS 인덱스 → top-k 검색
- ✅ 설명에 "최근 유사사례 다수" 근거 추가 (시간 남으면)

### B6. 신고 + 트렌드 엔드포인트 — `main.py`

- **목표**: 신고는 이미 있음(`/api/report`) → 확인만. 트렌드 집계 추가
- **방법**: `/api/trends` 추가 → 평판DB에서 최다 신고 도메인·문구 집계 반환 (C 대시보드용)
- ✅ 신고→그래프 갱신 확인 + 트렌드 API 동작

### B7. A 모델 통합 확인

- **목표**: A가 `models/text_clf/`, `fusion.pkl` 올리면 재시작만으로 반영되는지
- ✅ 실모델 3종(문자·융합) 다 붙은 상태로 API 동작

### B8. 적대적 강건성 데모 경로

- **목표**: 키워드 필터가 놓치는 난독화 문자를 시스템이 잡는 케이스 확보
- ✅ 데모용 "함정" 문자 세트 + 정답 동작 확인

---

# C 트랙 — 프론트 · 데모

### C1. Vite React 세팅 — `frontend/`

- **목표**: 프로젝트 생성 + 백엔드 프록시
- **방법**: `npm create vite@latest frontend -- --template react` / `vite.config.js`에 `server.proxy['/api'] = 'http://localhost:8000'` / 실행은 `npm run dev -- --host`
- ✅ 프론트 뜨고 `/api/health` 프록시로 호출됨

### C2. API 클라이언트 — `src/api/client.js`

- **목표**: 계약대로 호출 함수 (계약 ①②③)
- **방법**:
    
    ```jsx
    export const analyze = (text, sender) =>
        fetch("/api/analyze", {method:"POST", headers:{"Content-Type":"application/json"},
          body: JSON.stringify({text, sender})}).then(r => r.json());
      export const getGraph = () => fetch("/api/graph").then(r => r.json());
      export const report = (text, sender) =>
        fetch("/api/report", {method:"POST", headers:{"Content-Type":"application/json"},
          body: JSON.stringify({text, sender})}).then(r => r.json());
    ```
    
- ✅ 세 함수 동작

### C3. 입력 화면 — `src/pages/Analyze.jsx`

- **목표**: 문자 textarea + 발신번호(선택) input + 분석 버튼
- ✅ 입력 → `analyze()` 호출 → 응답 받음

### C4. 결과 화면 — `src/components/Result.jsx`

- **목표**: 응답을 사람이 읽게 표시
- **방법**: (계약 ① 필드 그대로)
    - `risk_score`×100 → 게이지/퍼센트
    - `level` → 색 (safe=초록/suspicious=주황/danger=빨강)
    - `reasons` → 근거 리스트
    - `evidence` → 배지 (`type`+`detail`)
    - `signals` → 모델/규칙/평판 3개 바 (투명성)
    - `cluster` → **null 체크 후** "조직 N 연결, 신고 M건"
- ✅ 한 문자에 대해 위험도+근거+조직이 다 보임

### C5. 그래프 시각화 — `src/components/OrgGraph.jsx`

- **목표**: `/api/graph`를 force-graph로
- **방법**:
    
    ```jsx
    import ForceGraph2D from "react-force-graph-2d";
      // getGraph() → {nodes, edges, cluster_count}
      // ⚠️ 라이브러리는 links를 기대 → edges를 links로 매핑 (계약 ②)
      const data = { nodes: g.nodes, links: g.edges };
      // node color: type(number/url/phrase)별, group: cluster별
      <ForceGraph2D graphData={data} nodeAutoColorBy="cluster"
        nodeLabel={n => `${n.type}: ${n.label}`} />
    ```
    
- ✅ 노드가 밀집해 클러스터로 뭉치는 화면

### C6. 신고 버튼 → 신고 페이지 — `src/pages/Report.jsx`

- **목표**: 결과 화면 [신고하기] → 신고 페이지로 라우팅, 폼 프리필, 제출
- **방법**:
    - 결과 화면: `const nav = useNavigate(); <button onClick={() => nav("/report", {state:{text, sender}})}>신고하기</button>`
    - 신고 페이지: `useLocation().state`로 text/sender 프리필 → 확인/수정 → `report()` 제출 → "신고 완료, 평판DB 반영됨" + `getGraph()` 새로고침해 노드 증가 보여주기
- ✅ 분석→신고→그래프 갱신까지 흐름 완성

### C7. 트렌드 대시보드 — `src/pages/Trends.jsx`

- **목표**: `/api/trends`로 최다 신고 문구·URL·사칭기관 시각화 (차트)
- ✅ 대시보드 동작

### C8. 데모 시나리오 + 발표덱 (총괄)

- **목표**: 골든패스 스크립트화 + 덱 + 리허설 + 녹화 백업
- ✅ 2분 라이브 데모 완성

---

## 트랙 간 동기화 (누가 뭘 기다리나)

| 이 작업 | 필요조건 | 그전엔 이걸로 |
| --- | --- | --- |
| C4 결과화면 | 없음 (스켈레톤 폴백이 응답 줌) | 바로 시작 가능 |
| C5 그래프 | 없음 (시드로 그래프 나옴) | 바로 시작 가능 |
| B7 모델통합 | A6 (모델 저장) | 폴백으로 개발 |
| A9 융합학습 | B1~B2 (신호 추출 가능) | 가중합으로 개발 |
| A10 평가 | A9 + B 신호 완성 | — |

**핵심 원칙**: 아무도 남을 안 기다림. 스켈레톤이 전부 폴백으로 응답을 주니까, A가 학습하는 동안 B·C는 실제 데이터 없이도 자기 화면·로직을 완성한다. 실모델은 **인터페이스 뒤에서 조용히 교체**될 뿐.

### 관통 마일스톤 (이거 되면 절반 성공)

W1 말까지: 세 트랙을 붙여서 **문자 붙여넣기 → 위험도+근거+그래프 → 신고 → 그래프 갱신** 이 스텁으로라도 한 번 끝까지 돌아가게. 이후는 각 부분 품질 올리기.

## 🚨 신고 기능 (Report)

### 개요

- 신고는 **2종류**: ① PhishGuard DB에 신고(메인, 우리 차별점) ② 공식 기관에 신고(외부 링크)
- **AI 자동 판단은 DB에 저장 안 함.** 사용자가 신고 버튼 누른 것만 저장 → 평판DB 신뢰도 유지
- (선택) 위험 문자는 `pending(후보)`로 자동 수집 → 신고/다수확인 시 `확정` 승격

### ✅ 백엔드 (B) 할 일

- [ ]  `POST /api/report` 동작 확인 (이미 구현됨 — 신고 시 DB 저장 + 그래프 갱신)
- [ ]  `AnalyzeResponse`에 `urls: list[str]` 필드 추가 (프론트 신고문구용)
- [ ]  `analyze.py`에서 `urls=pre["urls"]` 채워서 응답에 포함
- [ ]  C에게 "urls 필드 추가함" 공지 (INTEGRATION 계약 ① 갱신)
- [ ]  (선택) `reputation.py`에 pending 테이블 추가 — 후보/확정 분리

### ✅ 프론트 (C) 할 일

- [ ]  신고 문구 자동생성 함수 `buildReportText()`
- [ ]  신고 섹션 UI: 문구 미리보기(textarea) + 버튼 3개
- [ ]  버튼 동작: 우리 DB 신고 / 복사+공식사이트 이동
- [ ]  결과 화면에 [신고하기] → 신고 섹션 연결

### 🔘 버튼 3개 정리

| 버튼 | 동작 | 이동/대상 |
| --- | --- | --- |
| **PhishGuard에 신고** | `POST /api/report` 호출 → 우리 DB 저장 | (내부, 이동 없음) |
| **KISA 스팸신고로 이동** | 신고문구 복사 + 새 탭 열기 | `https://spam.kisa.or.kr` |

### 🔗 공식 신고처 (참고)

- **통합신고센터** `counterscam112.go.kr` — 과기정통부·방통위·금융위·경찰청·KISA·금감원 신고 기능을 통합한 누리집 (기본값) [AI-Hub](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=271)
- **KISA 불법스팸대응센터** `spam.kisa.or.kr` — 인터넷 신고, 전화는 국번없이 118 [Kca](https://www.kca.go.kr/home/board/download.do?menukey=6102&fno=10030289&bid=00000160&did=1003140655)

### 📋 신고 문구 템플릿

`[스미싱 의심 신고]

■ 수신 문자 내용
{문자 본문}

■ 발신번호
{sender 또는 "미상"}

■ 포함된 의심 URL
{url 목록 또는 "없음"}

■ 신고 사유
PhishGuard AI 분석 결과 위험도 {risk_score}%로 스미싱이 의심됩니다.
{탐지 근거 상위 3개}

■ 수신 일시
{현재 날짜/시간}`