"""규칙 엔진 (계약 ⑤).

    rules.analyze(pre: dict) -> (score: float, evidence: list[dict])

evidence 원소는 항상 {"type": str, "detail": str, "weight": float} (계약 통일).
score 는 0~1. 이 evidence 가 그대로 /api/analyze 로 나가고 explain 입력이 됨.

지금 규칙 (whois 도메인 나이는 B1에서 추가 예정):
  1) 피싱 URL 명단 조회 (seed/phishing_urls.txt)
  2) 단축 URL 탐지
  3) 의심 TLD 탐지
  4) 행동 유도 키워드
"""

import os

import config

# --- 단축 URL 도메인 -----------------------------------------------------
_SHORTENERS = {
    "bit.ly", "tinyurl.com", "is.gd", "goo.gl", "t.co", "ow.ly",
    "buly.kr", "han.gl", "url.kr", "vo.la", "me2.do", "durl.kr",
    "abr.ge", "me2.kr", "muz.so",
}

# --- 의심 TLD (스미싱에서 흔히 쓰이는 저가/신규 gTLD) --------------------
_SUSPICIOUS_TLDS = {
    "top", "xyz", "click", "link", "info", "online", "yachts",
    "country", "zip", "mov", "gq", "cf", "tk", "ml", "ga", "work",
    "rest", "cyou", "sbs", "quest",
}

# --- 행동 유도 키워드 (detail 로 매칭된 단어를 그대로 노출) --------------
# 가중치는 낮게 — 명단 히트가 지배하도록. 여러 개 겹치면 누적되되 1로 클램프.
_KEYWORDS = {
    "무료": 0.05, "당첨": 0.10, "클릭": 0.08, "조회": 0.06,
    "인증": 0.08, "계좌": 0.10, "송금": 0.12, "이체": 0.10,
    "정지": 0.10, "압류": 0.12, "체납": 0.10, "미납": 0.10,
    "고객센터": 0.05, "확인요망": 0.10, "긴급": 0.08, "즉시": 0.06,
    "주소불일치": 0.12, "본인확인": 0.08, "안내": 0.03, "환급": 0.08,
}

# 규칙별 가중치
_W_BLOCKLIST = 0.5
_W_SHORTENER = 0.2
_W_SUSPICIOUS_TLD = 0.15


def _load_blocklist(path: str) -> set[str]:
    """seed 파일에서 피싱 도메인 명단 로드. 주석(#)·빈 줄 무시. 소문자."""
    domains: set[str] = set()
    if not os.path.exists(path):
        return domains
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            domains.add(line.lower())
    return domains


# 모듈 로드 시 1회 읽어 캐시 (B1에서 파일 교체하면 서버 재시작으로 반영)
_BLOCKLIST = _load_blocklist(config.PHISHING_URLS_PATH)


def _tld_of(domain: str) -> str:
    """도메인의 최상위 라벨(TLD) 반환. 예: free.top -> top"""
    parts = domain.rsplit(".", 1)
    return parts[-1] if len(parts) == 2 else ""


def analyze(pre: dict) -> tuple[float, list[dict]]:
    """pre dict -> (score 0~1, evidence list). 계약 ⑤."""
    domains = pre.get("domains", []) or []
    norm = pre.get("norm", "") or ""

    score = 0.0
    evidence: list[dict] = []

    # 1) 피싱 URL 명단 조회
    for d in domains:
        if d in _BLOCKLIST:
            score += _W_BLOCKLIST
            evidence.append({
                "type": "피싱 URL 명단",
                "detail": d,
                "weight": _W_BLOCKLIST,
            })

    # 2) 단축 URL 탐지
    for d in domains:
        if d in _SHORTENERS:
            score += _W_SHORTENER
            evidence.append({
                "type": "단축 URL",
                "detail": d,
                "weight": _W_SHORTENER,
            })

    # 3) 의심 TLD 탐지 (명단에 이미 걸린 도메인은 중복 계상 안 함)
    for d in domains:
        if d in _BLOCKLIST:
            continue
        tld = _tld_of(d)
        if tld in _SUSPICIOUS_TLDS:
            score += _W_SUSPICIOUS_TLD
            evidence.append({
                "type": "의심 TLD",
                "detail": f".{tld} ({d})",
                "weight": _W_SUSPICIOUS_TLD,
            })

    # 4) 행동 유도 키워드
    for kw, w in _KEYWORDS.items():
        if kw in norm:
            score += w
            evidence.append({
                "type": "행동 유도 문구",
                "detail": kw,
                "weight": w,
            })

    return round(min(score, 1.0), 4), evidence
