from __future__ import annotations

from typing import Any

from ai.src.url_features import extract_url_features


# ============================================================
# Validation에서 확정한 규칙 가중치
# ============================================================

W_IP_ADDRESS = 0.30
W_SHORTENER = 0.25
W_SUSPICIOUS_TLD = 0.20
W_PUNYCODE = 0.20
W_AT_SYMBOL = 0.25

W_HIGH_DIGIT_RATIO = 0.15
W_MEDIUM_DIGIT_RATIO = 0.08

W_MANY_SUBDOMAINS = 0.15
W_MULTIPLE_SUBDOMAINS = 0.08

# 독립 구조 규칙만으로 피싱 후보를 판단할 때 사용할 기준
URL_RULE_THRESHOLD = 0.20


# ============================================================
# evidence 생성 보조 함수
# ============================================================

def _evidence(
    evidence_type: str,
    detail: str,
    weight: float,
) -> dict[str, Any]:
    """
    백엔드 계약과 동일한 evidence 형식으로 반환한다.
    """
    return {
        "type": evidence_type,
        "detail": detail,
        "weight": round(float(weight), 4),
    }


# ============================================================
# URL 한 개 분석
# ============================================================

def analyze_url(
    url: str,
) -> tuple[float, list[dict[str, Any]]]:
    """
    블록리스트를 사용하지 않고 URL 구조만 분석한다.

    반환:
        score: 0~1 구조 위험 점수
        evidence: 탐지 근거 목록
    """
    features = extract_url_features(url)

    score = 0.0
    evidence: list[dict[str, Any]] = []

    # --------------------------------------------------------
    # 강한 구조 신호
    # --------------------------------------------------------

    if features["has_ip_address"] >= 1:
        score += W_IP_ADDRESS
        evidence.append(
            _evidence(
                "IP 주소 직접 사용",
                "도메인 대신 IP 주소가 사용되었습니다.",
                W_IP_ADDRESS,
            )
        )

    if features["is_shortener"] >= 1:
        score += W_SHORTENER
        evidence.append(
            _evidence(
                "단축 URL",
                "실제 접속 주소를 숨길 수 있는 단축 URL입니다.",
                W_SHORTENER,
            )
        )

    if features["is_suspicious_tld"] >= 1:
        score += W_SUSPICIOUS_TLD
        evidence.append(
            _evidence(
                "의심 TLD",
                "피싱 데이터에서 반복적으로 나타난 TLD가 사용되었습니다.",
                W_SUSPICIOUS_TLD,
            )
        )

    if features["has_punycode"] >= 1:
        score += W_PUNYCODE
        evidence.append(
            _evidence(
                "Punycode",
                "유사 문자 도메인에 사용될 수 있는 Punycode가 포함되었습니다.",
                W_PUNYCODE,
            )
        )

    if features["at_count"] >= 1:
        score += W_AT_SYMBOL
        evidence.append(
            _evidence(
                "URL 주소 은폐",
                "@ 문자가 포함되어 실제 접속 도메인을 혼동시킬 수 있습니다.",
                W_AT_SYMBOL,
            )
        )

    # --------------------------------------------------------
    # 숫자 비율
    # --------------------------------------------------------

    host_digit_ratio = float(
        features["host_digit_ratio"]
    )

    if host_digit_ratio >= 0.20:
        score += W_HIGH_DIGIT_RATIO
        evidence.append(
            _evidence(
                "도메인 숫자 비율",
                (
                    "도메인 내 숫자 비율이 "
                    f"{host_digit_ratio:.1%}로 높습니다."
                ),
                W_HIGH_DIGIT_RATIO,
            )
        )

    elif host_digit_ratio >= 0.10:
        score += W_MEDIUM_DIGIT_RATIO
        evidence.append(
            _evidence(
                "도메인 숫자 비율",
                (
                    "도메인 내 숫자 비율이 "
                    f"{host_digit_ratio:.1%}입니다."
                ),
                W_MEDIUM_DIGIT_RATIO,
            )
        )

       # --------------------------------------------------------
    # 서브도메인 수
    # --------------------------------------------------------

    subdomain_count = int(
        features["subdomain_count"]
    )

    # IP 주소의 점(.)은 서브도메인 구분자가 아니므로
    # IP 주소에는 서브도메인 가중치를 추가하지 않는다.
    if features["has_ip_address"] < 1:
        if subdomain_count >= 3:
            score += W_MANY_SUBDOMAINS
            evidence.append(
                _evidence(
                    "과도한 서브도메인",
                    f"서브도메인이 {subdomain_count}개 사용되었습니다.",
                    W_MANY_SUBDOMAINS,
                )
            )

        elif subdomain_count >= 2:
            score += W_MULTIPLE_SUBDOMAINS
            evidence.append(
                _evidence(
                    "다중 서브도메인",
                    f"서브도메인이 {subdomain_count}개 사용되었습니다.",
                    W_MULTIPLE_SUBDOMAINS,
                )
            )

    return (
        round(min(score, 1.0), 4),
        evidence,
    )


# ============================================================
# 전처리 결과 전체 분석
# ============================================================

def analyze(
    pre: dict,
) -> tuple[float, list[dict[str, Any]]]:
    """
    ai.preprocess.preprocess() 결과를 입력받아
    문자 안의 URL 구조 위험도를 계산한다.

    백엔드 담당자가 그대로 호출할 수 있는 형태:

        rule_s, rule_ev = url_rule_engine.analyze(pre)
    """
    urls = pre.get("urls", []) or []

    # 같은 URL이 반복된 경우 한 번만 분석
    unique_urls = list(
        dict.fromkeys(
            str(url).strip()
            for url in urls
            if str(url).strip()
        )
    )

    total_score = 0.0
    all_evidence: list[dict[str, Any]] = []

    for url in unique_urls:
        url_score, url_evidence = analyze_url(url)

        total_score += url_score

        for item in url_evidence:
            evidence_item = dict(item)
            evidence_item["detail"] = (
                f"{evidence_item['detail']} ({url})"
            )
            all_evidence.append(evidence_item)

    return (
        round(min(total_score, 1.0), 4),
        all_evidence,
    )


def is_suspicious(
    url: str,
    threshold: float = URL_RULE_THRESHOLD,
) -> bool:
    """
    URL 한 개가 확정 임계값 이상인지 반환한다.
    """
    score, _ = analyze_url(url)
    return score >= threshold


# ============================================================
# 단독 실행 테스트
# ============================================================

if __name__ == "__main__":
    test_urls = [
        "https://www.kbstar.com",
        "http://kb-secure-login.xyz/verify?id=1234",
        "https://bit.ly/test123",
        "http://192.168.0.1/login",
    ]

    for test_url in test_urls:
        score, evidence = analyze_url(test_url)

        print("=" * 80)
        print("URL:", test_url)
        print("점수:", score)
        print(
            "의심 여부:",
            score >= URL_RULE_THRESHOLD,
        )
        print("근거:")

        for item in evidence:
            print(item)