# 통합 계약서 (Integration Contract)

> 3명이 따로 개발 → 합칠 때 **어긋나면 터지는 지점**만 고정한 문서.
1일차에 다 같이 합의하고, 변경은 **관련된 두 사람 동의 후에만.**
아래 필드·함수명은 전부 실제 스켈레톤 코드와 일치함.
> 

---

## 0. 시스템 한눈에 + 소유자

```
문자 → preprocess ─┬─ classifier   (A) 문자모델 점수
                   ├─ rules        (B) URL명단+규칙 점수·증거
                   ├─ reputation   (B) 신고이력 점수·증거
                   └─ graph        (B) 조직 클러스터
                        → fusion   (A) 최종 위험도
                        → explain  (B) 근거 생성
                        → API      (B) → 프론트 (C)
```

| 담당 | 소유 파일 |
| --- | --- |
| **A** (모델·데이터·평가) | `classifier.py`, `fusion.py`, 학습 스크립트, 평가 |
| **B** (백엔드·인텔리전스) | `rules.py`, `reputation.py`, `graph.py`, `explain.py`, `main.py` |
| **C** (프론트·데모) | React 전체, 그래프 시각화, 신고 페이지 |
| **공통** (아무나 못 바꿈) | `schemas.py`, `preprocess.py`, `config.py` |

---

## 1. 통합 계약은 3층 · 7개

```
┌─ 외부 계약 (프론트 ↔ 백엔드) ─── ①API ②그래프형식 ③신고
├─ 내부 계약 (백엔드 A ↔ B) ──── ④pre키 ⑤함수시그니처 ⑥라벨
└─ 환경 계약 (전원) ──────────── ⑦포트·CORS·키·경로
```

---

## 2. 외부 계약 — 프론트(C) ↔ 백엔드(B)

### ① API `/api/analyze` — 제일 중요. 여기 어긋나면 전체가 안 붙음

**요청** `POST /api/analyze`

```json
{ "text": "문자 본문", "sender": "01012345678" }   // sender는 선택(null 가능)
```

**응답**

```json
{
  "risk_score": 0.56,          // 0~1 실수 (0~100 아님!)
  "level": "suspicious",       // "safe" | "suspicious" | "danger" 셋 중 하나
  "reasons": ["...", "..."],   // 사람이 읽는 근거 문장 배열
  "evidence": [{ "type": "단축 URL", "detail": "bit.ly", "weight": 0.2 }],
  "signals": { "model": 0.39, "rule": 0.6, "reputation": 0.4 },
  "cluster": { "id": "조직-0", "size": 6, "report_count": 5, "risk": 0.65 }
}                              // cluster는 null 가능 → 프론트에서 반드시 null 체크
```

**깨지기 쉬운 4곳 (여기만 조심하면 됨):**

- 필드명은 `snake_case` 고정 — `risk_score` (O), `riskScore` (X)
- 위험도 범위는 **0~1** — 화면에 %로 쓰려면 프론트가 ×100
- `level` 철자 3종 정확히 — "safe/suspicious/danger"
- `cluster`는 **null일 수 있음** — 조직 매칭 안 되면 없음

### ② 그래프 형식 `/api/graph`

**응답** `GET /api/graph`

```json
{
  "nodes": [{ "id": "url:xnr.ae1t.yachts", "label": "xnr.ae1t.yachts",
              "type": "url", "cluster": 0 }],
  "edges": [{ "source": "url:...", "target": "num:..." }],
  "cluster_count": 3
}
```

- `type` 값: `"number"` | `"url"` | `"phrase"` → C가 이걸로 노드 색 구분
- `cluster`(정수) → C가 이걸로 그룹/색 묶음
- C의 라이브러리(react-force-graph)가 기대하는 `{nodes, links}` 형식과 매핑 규칙을 1일차에 확정 (edges→links 이름만 바꾸면 됨)

### ③ 신고 `/api/report`

**요청** `POST /api/report` → `{ "text": "...", "sender": "..." }`**응답** → `{ "ok": true, "cluster_count": 4 }`

- 프론트: 신고 완료 표시 + (데모 효과) 그래프 새로고침 → 노드 실시간 증가

---

## 3. 내부 계약 — 백엔드 A ↔ B

### ④ 전처리 결과 `pre` dict 키 (모두가 공유 — 키 하나 바뀌면 다 깨짐)

`preprocess(text, sender)` 가 반환하는 dict. **A도 B도 이 키를 씀:**

| 키 | 용도 | 쓰는 사람 |
| --- | --- | --- |
| `pre["masked"]` | URL 가린 텍스트 (분류기 입력) | A |
| `pre["urls"]`, `pre["domains"]` | URL·도메인 | B(규칙·평판) |
| `pre["tokens"]` | 문구 토큰 (유사도) | B(평판·그래프) |
| `pre["sender"]` | 발신번호 | B |
| `pre["norm"]` | 정규화 원문 | B(키워드) |

### ⑤ 함수 시그니처 (이거 안 맞으면 `analyze.py`에서 에러)

```python
classifier.predict_proba(masked_text: str) -> float          # 0~1,  A
rules.analyze(pre: dict)      -> (score: float, evidence: list[dict])   # B
reputation.lookup(pre: dict)  -> (score: float, evidence: list[dict])   # B
graph.match_cluster(pre: dict)-> dict | None                 # B
fusion.fuse(model_p, rule_s, rep_s: float) -> float          # A
fusion.level(score: float)    -> str                         # A
```

- `evidence`의 각 원소는 항상 `{"type": str, "detail": str, "weight": float}` — 이 형식이 그대로 `/api/analyze`의 evidence로 나가고 explain의 입력이 됨. **형식 통일 필수.**

### ⑥ 라벨 규약 (A 내부지만 평가까지 영향)

- 학습·평가 전부 **`0 = 정상`, `1 = 피싱`** 로 통일
- meal-bbang `class` 컬럼(1/2/3) → 이 0/1로 어떻게 매핑할지 **팀 합의 후 고정** (예: 1→0 정상, 2→1 피싱, 3→처리방침 결정)
- 여기 어긋나면 모든 성능 수치가 뒤집힘

---

## 4. 환경 계약 — 전원

### ⑦ 포트 · CORS · 키 · 경로 (`config.py`에 이미 세팅)

| 항목 | 값 | 주의 |
| --- | --- | --- |
| 백엔드 포트 | 8000 |  |
| 프론트 포트 | 5173 (Vite) |  |
| CORS 허용 | `localhost:5173` | 안 맞으면 브라우저 호출 차단 |
| API 키 | `ANTHROPIC_API_KEY` (환경변수) | **`.env`에 두고 git 추적 금지** |
| 문자모델 경로 | `models/text_clf/` | A 저장 = B 로드, 같은 값 |
| 융합모델 경로 | `models/fusion.pkl` | 동일 |
| 임계값 | suspicious ≥ 0.40, danger ≥ 0.70 | A가 PR커브로 확정 |

---

## 5. 통합 순서 — 언제 합치나 (통합을 막판에 미루지 않기)

| 시점 | 할 일 |
| --- | --- |
| **1일차** | 이 문서 ①~⑦ 다 같이 합의 → 각자 병렬 시작 |
| **W1 말** | `analyze.py`에서 스텁으로 한 번 관통 (붙여넣기→점수 끝까지) |
| **W2 말** | 실제 모델·설명·그래프 끼워 골든패스 완성 |
| **W3** | 평가·강건성 + 프론트 완성도 |
| **W4** | 데모 리허설 |

---

## 6. 1일차 합의 체크리스트

- [ ]  `/api/analyze` 요청·응답 JSON 확정 (필드명·범위·null 규칙)
- [ ]  `/api/graph` 형식 확정 (edges↔links 매핑)
- [ ]  `/api/report` 요청·응답 확정
- [ ]  `pre` dict 키 목록 확정
- [ ]  신호 함수 5개 시그니처 확정
- [ ]  `evidence` 형식 `{type,detail,weight}` 확정
- [ ]  라벨 0/1 매핑 규칙 확정 (class 3 처리 포함)
- [ ]  포트·CORS·키 위치·모델 경로 확정
- [ ]  `.env` git 추적 제외 확인 (`git ls-files`)

---

## 7. 자주 깨지는 지점 (합칠 때 이 증상 나오면 여기부터 봐라)

| 증상 | 원인 | 확인할 계약 |
| --- | --- | --- |
| 프론트가 응답 파싱 실패 | 필드명·범위 불일치 | ① |
| 위험도가 이상하게 큼/작음 | 0~1 vs 0~100 혼동 | ① |
| 그래프가 안 그려짐 | edges/links, type/cluster 이름 | ② |
| `analyze.py`에서 에러 | 함수 시그니처·evidence 형식 | ⑤ |
| 신호 하나가 항상 0 | `pre` 키 오타/누락 | ④ |
| 평가 수치가 반대로 | 라벨 0/1 반전 | ⑥ |
| 브라우저에서 호출 막힘(CORS) | 포트·오리진 불일치 | ⑦ |