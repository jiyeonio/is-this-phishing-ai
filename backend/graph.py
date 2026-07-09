"""조직 클러스터 그래프 (계약 ②, ⑤).

    graph.match_cluster(pre: dict) -> dict | None
    graph.to_json()               -> {nodes, edges, cluster_count}  (계약 ②)

신고 이력(reputation.get_reports())에서 세 종류 노드를 만든다:
  - url    : 도메인            id "url:<domain>"
  - number : 발신번호(sender)  id "num:<sender>"    (sender 있을 때만)
  - phrase : 의미 있는 문구 토큰 id "phrase:<token>"

같은 신고 안에서 공유되는 요소(도메인/번호/문구)로 신고들을 연결(union-find)해
연결요소 = 조직 클러스터. 각 노드에 정수 cluster 부여.

초기 시드엔 sender 가 전부 null 이라 url·phrase 노드만 생김.
유저가 신고하면 sender 가 저장되므로 그때부터 number 노드도 생성됨.

⚠️ 범용어(확인/조회/안내 등)를 문구 노드로 쓰면 조직이 하나로 뭉개짐 →
STOPWORDS + 최소 길이로 걸러 조직별 분리를 유지 (아래 값은 튜닝 가능).
"""

import config
from backend import reputation

# phrase 노드에서 제외할 범용어 (마스킹 토큰 포함). 조직 식별력이 없는 단어들.
STOPWORDS = {
    "URL", "확인", "조회", "안내", "본인확인", "확인요망",
    "안내드립니다", "바랍니다", "있습니다", "드립니다",
}
_MIN_TOKEN_LEN = 2

# 문구만으로 클러스터를 인정할 최소 공유 토큰 수 (도메인·번호 매칭이 없을 때만).
# 클러스터 토큰 집합이 커서 자카드는 희석됨 → 공유 "개수"로 판정.
_MIN_SHARED_PHRASES = 2


# --- union-find --------------------------------------------------------
class _UF:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)  # 작은 루트로 — 순서 안정화


def _meaningful(tokens: list[str]) -> set[str]:
    return {
        t for t in tokens
        if len(t) >= _MIN_TOKEN_LEN and t not in STOPWORDS
    }


# 그래프는 서버 시작 후 1회 계산해 캐시 재사용. 신고로 데이터가 바뀌면
# invalidate() 로 캐시를 비워 다음 접근 때 다시 계산 (그래프만 갱신).
_CACHE: dict | None = None


def invalidate() -> None:
    """신고 등으로 신고 데이터가 바뀌었을 때 그래프 캐시를 비운다."""
    global _CACHE
    _CACHE = None


def _build() -> dict:
    """그래프 구조(캐시). 없으면 계산해 캐시에 저장."""
    global _CACHE
    if _CACHE is None:
        _CACHE = _compute()
    return _CACHE


def _compute() -> dict:
    """현재 신고들로 그래프 구조를 계산해 rich dict 반환.

    반환: {
      reports, report_cluster: list[int],
      nodes: list[node], edges: list[edge], cluster_count,
      clusters: {cid: {reports,domains,senders,tokens,size}},
    }
    """
    reports = reputation.get_reports()
    n = len(reports)

    # 신고별 요소 추출
    doms = [set(r["domains"]) for r in reports]
    sends = [r["sender"] for r in reports]
    phrs = [_meaningful(r["tokens"]) for r in reports]

    # 요소 → 그 요소를 가진 신고 인덱스 목록
    dom_idx: dict[str, list[int]] = {}
    send_idx: dict[str, list[int]] = {}
    tok_idx: dict[str, list[int]] = {}
    for i in range(n):
        for d in doms[i]:
            dom_idx.setdefault(d, []).append(i)
        if sends[i]:
            send_idx.setdefault(sends[i], []).append(i)
        for t in phrs[i]:
            tok_idx.setdefault(t, []).append(i)

    # 공유 요소로 신고 union
    uf = _UF(n)
    for group in (dom_idx, send_idx, tok_idx):
        for _, idxs in group.items():
            for j in range(1, len(idxs)):
                uf.union(idxs[0], idxs[j])

    # 연결요소 → 클러스터 정수 id (루트 순서대로 0..k-1)
    roots = sorted({uf.find(i) for i in range(n)})
    root_to_cid = {root: cid for cid, root in enumerate(roots)}
    report_cluster = [root_to_cid[uf.find(i)] for i in range(n)]

    # phrase 노드는 2건 이상 공유된 의미 토큰만 (싱글턴 클러터 방지)
    shared_tokens = {t for t, idxs in tok_idx.items() if len(idxs) >= 2}

    # --- 노드 --------------------------------------------------------
    nodes: list[dict] = []
    node_ids: set[str] = set()

    def _add_node(nid: str, label: str, ntype: str, cid: int) -> None:
        if nid in node_ids:
            return
        node_ids.add(nid)
        nodes.append({"id": nid, "label": label, "type": ntype, "cluster": cid})

    for d, idxs in dom_idx.items():
        _add_node(f"url:{d}", d, "url", report_cluster[idxs[0]])
    for s, idxs in send_idx.items():
        _add_node(f"num:{s}", s, "number", report_cluster[idxs[0]])
    for t in shared_tokens:
        idxs = tok_idx[t]
        _add_node(f"phrase:{t}", t, "phrase", report_cluster[idxs[0]])

    # --- 엣지 (신고별 star: 앵커→나머지 포함 노드) --------------------
    edge_set: set[tuple[str, str]] = set()
    for i in range(n):
        ents: list[str] = []
        ents += [f"url:{d}" for d in doms[i]]
        if sends[i]:
            ents.append(f"num:{sends[i]}")
        ents += [f"phrase:{t}" for t in phrs[i] if t in shared_tokens]
        ents = [e for e in ents if e in node_ids]
        if len(ents) < 2:
            continue
        anchor = ents[0]  # url 우선(위에서 url 먼저 넣음)
        for other in ents[1:]:
            key = tuple(sorted((anchor, other)))
            edge_set.add(key)
    edges = [{"source": a, "target": b} for a, b in sorted(edge_set)]

    # --- 클러스터 집계 ----------------------------------------------
    clusters: dict[int, dict] = {}
    for cid in range(len(roots)):
        clusters[cid] = {
            "reports": [], "domains": set(), "senders": set(),
            "tokens": set(), "size": 0,
        }
    for i in range(n):
        cid = report_cluster[i]
        c = clusters[cid]
        c["reports"].append(reports[i]["id"])
        c["domains"] |= doms[i]
        if sends[i]:
            c["senders"].add(sends[i])
        c["tokens"] |= phrs[i]
    for node in nodes:
        clusters[node["cluster"]]["size"] += 1

    return {
        "reports": reports,
        "report_cluster": report_cluster,
        "nodes": nodes,
        "edges": edges,
        "cluster_count": len(roots),
        "clusters": clusters,
    }


def _risk(report_count: int, domain_count: int) -> float:
    """클러스터 위험도 0~1. 신고 수·도메인 수가 많을수록 높음."""
    return round(min(0.95, 0.40 + 0.06 * report_count + 0.03 * domain_count), 4)


def to_json() -> dict:
    """계약 ② 형식으로 그래프 반환 (프론트 react-force-graph 용).

    {nodes:[{id,label,type,cluster}], edges:[{source,target}], cluster_count}
    """
    g = _build()
    return {
        "nodes": g["nodes"],
        "edges": g["edges"],
        "cluster_count": g["cluster_count"],
    }


def match_cluster(pre: dict) -> dict | None:
    """pre dict -> 매칭 클러스터 요약 dict | None (계약 ⑤).

    매칭 우선순위: 도메인 > 번호 > 문구 유사도. 아무것도 안 걸리면 None.
    반환: {id, size, report_count, risk}
    """
    g = _build()
    clusters = g["clusters"]
    if not clusters:
        return None

    in_doms = set(pre.get("domains", []) or [])
    in_send = pre.get("sender")
    in_toks = _meaningful(pre.get("tokens", []) or [])

    chosen: int | None = None

    # 1) 도메인 매칭 (가장 강함)
    best_overlap = 0
    for cid, c in clusters.items():
        ov = len(in_doms & c["domains"])
        if ov > best_overlap:
            best_overlap, chosen = ov, cid

    # 2) 번호 매칭
    if chosen is None and in_send:
        for cid, c in clusters.items():
            if in_send in c["senders"]:
                chosen = cid
                break

    # 3) 문구 매칭 (공유 토큰 개수 — 짧은 입력이라 자카드 대신 개수 기준)
    if chosen is None and in_toks:
        best_shared = 0
        for cid, c in clusters.items():
            shared = len(in_toks & c["tokens"])
            if shared > best_shared:
                best_shared, chosen = shared, cid
        if best_shared < _MIN_SHARED_PHRASES:
            chosen = None

    if chosen is None:
        return None

    c = clusters[chosen]
    return {
        "id": f"조직-{chosen}",
        "size": c["size"],
        "report_count": len(c["reports"]),
        "risk": _risk(len(c["reports"]), len(c["domains"])),
    }
