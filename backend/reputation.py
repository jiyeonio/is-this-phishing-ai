"""평판 DB + 조회 (계약 ⑤).

    reputation.lookup(pre: dict) -> (score: float, evidence: list[dict])

신고 이력(SQLite)에 근거해 위험 점수·증거를 냄. evidence 원소는 항상
{"type": str, "detail": str, "weight": float} (계약 통일).

DB(reputation.db)는 로컬에서 생성 — .gitignore 로 추적 제외.
서버 첫 기동 시 seed/reports.json 으로 시드(빈 경우에만).

우리 데이터엔 발신번호가 없어 sender 는 대부분 null → 매칭은 URL/도메인·문구
(토큰) 공유로 이뤄짐. 그래서 시드도 조직별로 URL·문구가 여러 신고에 공유됨.

저장소 역할도 겸함: graph.py 가 get_reports() 로 신고들을 읽어 클러스터를 만듦.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

import config
from ai.preprocess import preprocess

_DB_PATH = config.REPUTATION_DB_PATH

# 점수 가중치
_W_DOMAIN_HISTORY = 0.35   # 신고 이력에 있는 도메인
_W_PHRASE_SIMILAR = 0.30   # 유사 신고 문구 (토큰 자카드)
_W_PER_EXTRA_REPORT = 0.05  # 같은 도메인 신고 누적 보너스 (건당)
_SIMILARITY_THRESHOLD = 0.30  # 유사 문구로 인정하는 자카드 하한(토큰 자카드 기준 보정)

# 문구 유사도 계산에서 제외할 의미 없는 공통 토큰
_GENERIC_TOKENS = {
    "url",
    "http",
    "https",
    "www",
    "com",
    "net",
    "org",
}


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(_DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    """테이블 생성 + (비어 있으면) seed/reports.json 시드."""
    os.makedirs(os.path.dirname(_DB_PATH) or ".", exist_ok=True)
    con = _connect()
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                text       TEXT    NOT NULL,
                sender     TEXT,
                urls       TEXT    NOT NULL,   -- JSON 배열
                domains    TEXT    NOT NULL,   -- JSON 배열
                tokens     TEXT    NOT NULL,   -- JSON 배열
                source     TEXT    NOT NULL DEFAULT 'user',  -- 'seed'(시드) | 'user'(유저 신고)
                created_at TEXT    NOT NULL
            )
            """
        )
        con.commit()
        (count,) = con.execute("SELECT COUNT(*) FROM reports").fetchone()
        if count == 0:
            _seed(con)
    finally:
        con.close()


def _seed(con: sqlite3.Connection) -> None:
    if not os.path.exists(config.REPORTS_SEED_PATH):
        return
    with open(config.REPORTS_SEED_PATH, encoding="utf-8") as f:
        rows = json.load(f)
    for r in rows:
        _insert(con, r.get("text", ""), r.get("sender"), source="seed")
    con.commit()


def _insert(con: sqlite3.Connection, text: str, sender, source: str = "user"):
    """report 1건 삽입. text/sender 로 pre 를 뽑아 도메인·토큰까지 저장.

    source: 'seed'(시드 데이터) | 'user'(유저 신고, 기본값). 트렌드는 'user'만 셈.
    """
    pre = preprocess(text, sender)
    con.execute(
        "INSERT INTO reports (text, sender, urls, domains, tokens, source, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            text,
            pre["sender"],
            json.dumps(pre["urls"], ensure_ascii=False),
            json.dumps(pre["domains"], ensure_ascii=False),
            json.dumps(pre["tokens"], ensure_ascii=False),
            source,
            _now(),
        ),
    )


def add_report(text: str, sender=None) -> dict:
    """신고 저장 (/api/report). 저장된 report dict 반환. 유저 신고이므로 source='user'."""
    con = _connect()
    try:
        _insert(con, text, sender, source="user")
        con.commit()
        rid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        con.close()
    return {"id": rid, "text": text, "sender": sender}


def _row_to_dict(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "text": r["text"],
        "sender": r["sender"],
        "urls": json.loads(r["urls"]),
        "domains": json.loads(r["domains"]),
        "tokens": json.loads(r["tokens"]),
        "source": r["source"],
        "created_at": r["created_at"],
    }


def get_reports() -> list[dict]:
    """저장된 모든 신고(시드+유저)를 dict 리스트로 반환 (graph.py 가 소비)."""
    con = _connect()
    try:
        rows = con.execute(
            "SELECT id, text, sender, urls, domains, tokens, source, created_at "
            "FROM reports"
        ).fetchall()
    finally:
        con.close()
    return [_row_to_dict(r) for r in rows]


def get_reports_by_source(source: str) -> list[dict]:
    """특정 source('seed' | 'user')의 신고만 필터해 반환. 트렌드는 'user'만 사용."""
    con = _connect()
    try:
        rows = con.execute(
            "SELECT id, text, sender, urls, domains, tokens, source, created_at "
            "FROM reports WHERE source = ?",
            (source,),
        ).fetchall()
    finally:
        con.close()
    return [_row_to_dict(r) for r in rows]


def report_count() -> int:
    con = _connect()
    try:
        return con.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    finally:
        con.close()


def _clean_similarity_tokens(tokens) -> set[str]:
    """문구 유사도 계산에서 URL 공통 토큰과 빈 토큰을 제거."""
    cleaned: set[str] = set()

    for token in tokens or []:
        value = str(token).strip().lower()

        if not value:
            continue

        if value in _GENERIC_TOKENS:
            continue

        cleaned.add(value)

    return cleaned


def _jaccard(a: set, b: set) -> float:
    """의미 없는 URL 공통 토큰을 제외한 토큰 자카드 유사도."""
    clean_a = _clean_similarity_tokens(a)
    clean_b = _clean_similarity_tokens(b)

    # 토큰이 너무 적은 문장은 우연한 일치 가능성이 높아 제외
    if len(clean_a) < 3 or len(clean_b) < 3:
        return 0.0

    return len(clean_a & clean_b) / len(clean_a | clean_b)


def lookup(pre: dict) -> tuple[float, list[dict]]:
    """pre dict -> (score 0~1, evidence list). 계약 ⑤.

    - 신고 이력에 있는 도메인이면 가점(+ 신고 누적 보너스)
    - 저장된 신고와 문구(토큰) 유사도가 높으면 가점
    """
    in_domains = set(pre.get("domains", []) or [])
    in_tokens = set(pre.get("tokens", []) or [])

    reports = get_reports()
    score = 0.0
    evidence: list[dict] = []

    # 1) 도메인 신고 이력
    domain_hits: dict[str, int] = {}
    for rep in reports:
        for d in rep["domains"]:
            if d in in_domains:
                domain_hits[d] = domain_hits.get(d, 0) + 1
    for d, n in domain_hits.items():
        w = round(min(_W_DOMAIN_HISTORY + _W_PER_EXTRA_REPORT * (n - 1), 0.6), 4)
        score += w
        evidence.append(
            {
                "type": "신고 이력 도메인",
                "detail": f"{d} (신고 {n}건)",
                "weight": w,
            }
        )

    # 2) 유사 신고 문구 (토큰 자카드) — 도메인 매칭과 별개로 문구만 유사한 경우
    best_sim = 0.0
    for rep in reports:
        sim = _jaccard(in_tokens, set(rep["tokens"]))
        if sim > best_sim:
            best_sim = sim
    if best_sim >= _SIMILARITY_THRESHOLD:
        w = round(
            min(
                _W_PHRASE_SIMILAR * best_sim / _SIMILARITY_THRESHOLD,
                _W_PHRASE_SIMILAR,
            ),
            4,
        )
        score += w
        evidence.append(
            {
                "type": "유사 신고 문구",
                "detail": f"기존 신고와 {round(best_sim * 100)}% 유사",
                "weight": w,
            }
        )

    return round(min(score, 1.0), 4), evidence


# 모듈 로드 시 DB 준비 (테이블 + 시드)
init_db()