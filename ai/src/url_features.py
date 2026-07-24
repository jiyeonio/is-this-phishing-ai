from __future__ import annotations

import math
import re
from collections import Counter
from urllib.parse import parse_qs, urlparse

import pandas as pd


# ============================================================
# 1. 기본 목록
# ============================================================

SHORTENER_DOMAINS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "url.kr",
    "han.gl",
    "buly.kr",
    "vo.la",
    "c11.kr",
    "me2.do",
    "t.ly",
    "shorturl.at",
}

SUSPICIOUS_TLDS = {
    # 기존 일반 의심 TLD
    "xyz",
    "top",
    "click",
    "link",
    "info",
    "online",
    "yachts",
    "work",
    "rest",
    "cyou",
    "site",
    "art",
    "buzz",
    "shop",
    "cam",

    # Train 데이터에서 반복적으로 나타난 2차 후보
    # 국가 코드 TLD는 제외함
    "one",
    "life",
    "boats",
    "bar",
    "mom",
    "cfd",
    "icu",
    "sbs",
    "golf",
    "hair",
    "run",
    "lol",
    "world",
    "digital",
    "loan",
    "homes",
    "ink",
    "skin",
    "makeup",
    "email",
}

SUSPICIOUS_WORDS = {
    "login",
    "verify",
    "secure",
    "account",
    "update",
    "confirm",
    "password",
    "bank",
    "card",
    "delivery",
    "parcel",
    "refund",
    "payment",
    "auth",
    "signin",
    "security",
    "support",
    "wallet",
}


# ============================================================
# 2. 보조 함수
# ============================================================

def ensure_scheme(url: object) -> str:
    """
    URL에 프로토콜이 없으면 파싱을 위해 http://를 붙인다.
    """
    value = str(url).strip().lower()

    if not value:
        return ""

    if not re.match(
        r"^[a-z][a-z0-9+.-]*://",
        value,
    ):
        value = "http://" + value

    return value


def calculate_entropy(value: str) -> float:
    """
    문자열의 문자 다양성을 엔트로피로 계산한다.
    무작위 문자열처럼 복잡할수록 값이 높아질 수 있다.
    """
    if not value:
        return 0.0

    counts = Counter(value)
    length = len(value)

    entropy = 0.0

    for count in counts.values():
        probability = count / length
        entropy -= probability * math.log2(
            probability
        )

    return float(entropy)


def is_ip_address(host: str) -> int:
    """
    도메인 대신 IPv4 주소를 직접 사용했는지 확인한다.
    """
    ipv4_pattern = re.compile(
        r"^(?:\d{1,3}\.){3}\d{1,3}$"
    )

    if not ipv4_pattern.fullmatch(host):
        return 0

    parts = host.split(".")

    return int(
        all(
            0 <= int(part) <= 255
            for part in parts
        )
    )


def count_suspicious_words(value: str) -> int:
    """
    URL 문자열에 의심 단어가 몇 종류 포함됐는지 계산한다.
    """
    lower_value = value.lower()

    return sum(
        1
        for word in SUSPICIOUS_WORDS
        if word in lower_value
    )


# ============================================================
# 3. URL 하나의 특징 추출
# ============================================================

def extract_url_features(
    url: object,
) -> dict[str, float]:
    normalized_url = ensure_scheme(url)

    try:
        parsed = urlparse(
            normalized_url
        )
    except ValueError:
        parsed = urlparse(
            "http://invalid.local"
        )

    host = (
        parsed.hostname
        or ""
    ).lower()

    path = parsed.path or ""
    query = parsed.query or ""
    fragment = parsed.fragment or ""

    full_value = normalized_url.lower()

    host_without_www = (
        host.removeprefix("www.")
    )

    # --------------------------------------------------------
    # 도메인 전용 통계
    # --------------------------------------------------------

    host_length = len(
        host_without_www
    )

    host_digit_count = sum(
        character.isdigit()
        for character in host_without_www
    )

    host_letter_count = sum(
        character.isalpha()
        for character in host_without_www
    )

    host_hyphen_count = (
        host_without_www.count("-")
    )

    host_digit_ratio = (
        host_digit_count / host_length
        if host_length
        else 0.0
    )

    host_letter_ratio = (
        host_letter_count / host_length
        if host_length
        else 0.0
    )

    domain_parts = [
        part
        for part in host_without_www.split(".")
        if part
    ]

    max_domain_label_length = max(
        (
            len(part)
            for part in domain_parts
        ),
        default=0,
    )

    tld = (
        domain_parts[-1]
        if domain_parts
        else ""
    )

    subdomain_count = max(
        len(domain_parts) - 2,
        0,
    )

    # --------------------------------------------------------
    # URL 전체 통계
    # --------------------------------------------------------

    digit_count = sum(
        character.isdigit()
        for character in full_value
    )

    letter_count = sum(
        character.isalpha()
        for character in full_value
    )

    special_count = sum(
        not character.isalnum()
        for character in full_value
    )

    url_length = len(
        full_value
    )

    digit_ratio = (
        digit_count / url_length
        if url_length
        else 0.0
    )

    letter_ratio = (
        letter_count / url_length
        if url_length
        else 0.0
    )

    special_ratio = (
        special_count / url_length
        if url_length
        else 0.0
    )

    query_params = parse_qs(
        query,
        keep_blank_values=True,
    )

    # --------------------------------------------------------
    # 특징 결과
    # --------------------------------------------------------

    features = {
        # 전체 URL 길이
        "url_length": float(
            url_length
        ),

        # 도메인 전용 특징
        "host_length": float(
            host_length
        ),
        "host_digit_count": float(
            host_digit_count
        ),
        "host_digit_ratio": float(
            host_digit_ratio
        ),
        "host_letter_ratio": float(
            host_letter_ratio
        ),
        "host_hyphen_count": float(
            host_hyphen_count
        ),
        "max_domain_label_length": float(
            max_domain_label_length
        ),

        # 경로·쿼리 길이
        "path_length": float(
            len(path)
        ),
        "query_length": float(
            len(query)
        ),
        "fragment_length": float(
            len(fragment)
        ),

        # 기호 개수
        "dot_count": float(
            full_value.count(".")
        ),
        "hyphen_count": float(
            full_value.count("-")
        ),
        "underscore_count": float(
            full_value.count("_")
        ),
        "slash_count": float(
            full_value.count("/")
        ),
        "question_count": float(
            full_value.count("?")
        ),
        "equal_count": float(
            full_value.count("=")
        ),
        "ampersand_count": float(
            full_value.count("&")
        ),
        "at_count": float(
            full_value.count("@")
        ),
        "percent_count": float(
            full_value.count("%")
        ),

        # 전체 URL 문자 비율
        "digit_count": float(
            digit_count
        ),
        "digit_ratio": float(
            digit_ratio
        ),
        "letter_ratio": float(
            letter_ratio
        ),
        "special_ratio": float(
            special_ratio
        ),

        # 도메인 구조
        "domain_part_count": float(
            len(domain_parts)
        ),
        "subdomain_count": float(
            subdomain_count
        ),
        "query_param_count": float(
            len(query_params)
        ),

        # 이진 특징
        "has_https": float(
            parsed.scheme == "https"
        ),
        "has_ip_address": float(
            is_ip_address(
                host_without_www
            )
        ),
        "has_port": float(
            parsed.port is not None
            if host
            else False
        ),
        "has_punycode": float(
            "xn--" in host_without_www
        ),

        "is_shortener": float(
            host_without_www
            in SHORTENER_DOMAINS
            or any(
                host_without_www.endswith(
                    "." + domain
                )
                for domain in SHORTENER_DOMAINS
            )
        ),

        "is_suspicious_tld": float(
            tld in SUSPICIOUS_TLDS
        ),

        "suspicious_word_count": float(
            count_suspicious_words(
                full_value
            )
        ),

        # 문자열 복잡도
        "host_entropy": float(
            calculate_entropy(
                host_without_www
            )
        ),

        "url_entropy": float(
            calculate_entropy(
                full_value
            )
        ),
    }

    return features


# ============================================================
# 4. 데이터프레임 전체 특징 추출
# ============================================================

def build_feature_dataframe(
    df: pd.DataFrame,
    url_column: str = "url",
) -> pd.DataFrame:
    if url_column not in df.columns:
        raise ValueError(
            f"URL 컬럼이 없습니다: {url_column}"
        )

    feature_rows = [
        extract_url_features(url)
        for url in df[url_column]
    ]

    feature_df = pd.DataFrame(
        feature_rows
    )

    return feature_df


# ============================================================
# 5. 간단 실행 테스트
# ============================================================

if __name__ == "__main__":
    examples = [
        "https://www.kbstar.com",
        "http://kb-secure-login.xyz/verify?id=1234",
        "https://bit.ly/test123",
        "http://192.168.0.1/login",
    ]

    for example in examples:
        print("=" * 80)
        print("URL:", example)
        print(
            extract_url_features(
                example
            )
        )