"""위협 트렌드 집계 (계약 ④ /api/trends).

    trends.get_trends() -> {top_phrases, top_urls}

⚠️ 유저 신고(source='user')만 센다. 시드(KISA·기본 시드)는 제외 →
유저 신고가 0이면 빈 배열이 나가고 프론트는 "아직 신고 없음" 빈 상태를 보인다.
("유저 0인데 트렌드에 숫자" 문제 방지.)

도메인은 graph 와 동일하게 등록도메인(eTLD+1)으로 접어 조직 단위로 집계하고,
문구는 graph 의 정규화 토큰(_norm_tokens: 조사 제거 + STOPWORDS)을 재사용해
조사 조각("절차를")·범용어·종결어를 제외하고 어간("절차")으로 합쳐 집계한다.
"""

from collections import Counter

from backend import graph, reputation

_TOP_N = 10


def _top(counter: Counter, n: int = _TOP_N) -> list[dict]:
    """빈도 상위 n개를 [{label, count}] 형태로 (프론트 normalize.js 계약)."""
    return [{"label": label, "count": count} for label, count in counter.most_common(n)]


def get_trends() -> dict:
    """유저 신고만 집계한 트렌드. {top_phrases, top_urls} (계약 ④)."""
    reports = reputation.get_reports_by_source("user")

    url_counter: Counter = Counter()
    phrase_counter: Counter = Counter()
    for r in reports:
        # 한 신고 안에서 같은 등록도메인 중복은 1회로 (신고 "건수" 기준 집계)
        for d in {graph._reg_domain(d) for d in r["domains"]}:
            if d:
                url_counter[d] += 1
        # graph 와 동일한 정규화(조사 제거 + STOPWORDS + 최소길이) 사용 →
        # "절차를"/"절차가"가 "절차"로 합쳐지고, 조사 조각·흔한 종결어는 걸러진다.
        for t in graph._norm_tokens(r["tokens"]):
            phrase_counter[t] += 1

    return {
        "top_phrases": _top(phrase_counter),
        "top_urls": _top(url_counter),
    }
