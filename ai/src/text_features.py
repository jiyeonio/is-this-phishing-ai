# src/text_features.py
# ============================================================
# 문자 전처리 및 URL/전화번호 위험 신호 추출
#
# 기존 방식:
#   모든 URL -> [URL]
#
# 수정 방식:
#   공식 URL   -> [URL_OFFICIAL]
#   단축 URL   -> [URL_SHORTENER]
#   기타 URL   -> [URL_SUSPICIOUS]
#
# 전화번호:
#   공식 번호  -> [PHONE_OFFICIAL]
#   휴대폰     -> [PHONE_MOBILE]
#   해외 번호  -> [PHONE_FOREIGN]
# ============================================================

from __future__ import annotations

import re
import unicodedata


# ============================================================
# 1. 공식 도메인
# ============================================================

OFFICIAL_DOMAINS = {
    # 택배
    "cjlogistics.com",
    "hanjin.com",
    "epost.go.kr",
    "coupang.com",
    "slx.co.kr",
    "lotteglogis.com",
    "ilogen.com",
    "kdexp.com",
    "ds3211.co.kr",
    "gspostbox.com",

    # 카드
    "kbcard.com",
    "shinhancard.com",
    "samsungcard.com",
    "hyundaicard.com",

    # 은행·금융
    "kbstar.com",
    "shinhan.com",
    "wooribank.com",
    "kakaobank.com",
    "toss.im",

    # 쇼핑·배달
    "baemin.com",
    "11st.co.kr",
    "gmarket.co.kr",

    # 공공기관
    "nhis.or.kr",
    "hometax.go.kr",
    "koroad.or.kr",

    # 통신사
    "tworld.co.kr",
    "kt.com",
}


# ============================================================
# 2. 단축 URL
# ============================================================

SHORTENER_DOMAINS = {
    "bit.ly",
    "me2.do",
    "han.gl",
    "url.kr",
    "buly.kr",
    "vo.la",
    "abit.ly",
    "c11.kr",
    "muz.so",
    "tuney.kr",
    "tinyurl.com",
}


# ============================================================
# 3. 공식 대표번호
# 숫자만 남긴 형태로 저장
# ============================================================

OFFICIAL_NUMBERS = {
    "15881255",  # CJ대한통운
    "15881300",  # 우체국
    "15777011",  # 쿠팡
    "16002882",  # SLX
    "15880011",  # 한진
    "15882121",  # 롯데택배
    "15889988",  # 로젠택배
    "18995368",  # 경동택배
    "15228783",  # 대신택배
    "15771287",  # GS Postbox
    "15881688",  # KB국민카드
    "15447000",  # 신한카드
    "15888700",  # 삼성카드
    "15776000",  # 현대카드
    "15889999",  # KB국민은행
    "15998000",  # 신한은행
    "15885000",  # 우리은행
    "15993333",  # 카카오뱅크
    "15994905",  # 토스
    "16000987",  # 배달의민족
    "15996001",  # 11번가
    "15665701",  # G마켓
    "15771000",  # 국민건강보험
    "126",       # 국세청
    "15771120",  # 도로교통공단
    "114",       # SKT
    "100",       # KT
}


# ============================================================
# 4. 정규식
# ============================================================

URL_PATTERN = re.compile(
    r"""
    (?:
        https?://[^\s<>"']+
        |
        www\.[^\s<>"']+
        |
        \b(?:[a-zA-Z0-9-]+\.)+
        (?:com|net|org|kr|co\.kr|go\.kr|or\.kr|io|me|im|ly|do|gl|
           xyz|top|cc|vip|click|buzz|shop)
        (?:/[^\s<>"']*)?
    )
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)

PHONE_PATTERN = re.compile(
    r"""
    (?<!\d)
    (?:
        \+\d{1,3}[-\s]?\d{3,4}[-\s]?\d{4}
        |
        0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}
        |
        1\d{3}[-\s]?\d{4}
        |
        010[-\s]?\d{3,4}[-\s]?\d{4}
    )
    (?!\d)
    """,
    flags=re.VERBOSE,
)


# ============================================================
# 5. URL 처리
# ============================================================

def extract_host(url: str) -> str:
    """URL에서 host 부분만 추출한다."""
    value = str(url).strip().lower()

    value = re.sub(r"^https?://", "", value)
    value = re.sub(r"^www\.", "", value)

    host = value.split("/", maxsplit=1)[0]
    host = host.split("?", maxsplit=1)[0]
    host = host.split("#", maxsplit=1)[0]
    host = host.rstrip(".,!?;:)]}\"'")

    return host


def is_domain_match(host: str, domain: str) -> bool:
    """
    정확한 도메인 또는 하위 도메인인지 확인한다.

    예:
        hanjin.com         -> True
        m.hanjin.com       -> True
        fakehanjin.com     -> False
    """
    return host == domain or host.endswith("." + domain)


def classify_url(url: str) -> str:
    host = extract_host(url)

    if any(is_domain_match(host, domain) for domain in OFFICIAL_DOMAINS):
        return " [URL_OFFICIAL] "

    if any(is_domain_match(host, domain) for domain in SHORTENER_DOMAINS):
        return " [URL_SHORTENER] "

    return " [URL_SUSPICIOUS] "


# ============================================================
# 6. 전화번호 처리
# ============================================================

def classify_phone(phone: str) -> str:
    value = str(phone).strip()
    digits = re.sub(r"\D", "", value)

    # 해외번호
    if value.startswith("+") and not digits.startswith("82"):
        return " [PHONE_FOREIGN] "

    # 공식번호 목록
    if digits in OFFICIAL_NUMBERS:
        return " [PHONE_OFFICIAL] "

    # 국내 휴대전화
    if digits.startswith("010"):
        return " [PHONE_MOBILE] "

    # 15xx, 16xx, 18xx 대표번호
    if re.fullmatch(r"(15|16|18)\d{6}", digits):
        return " [PHONE_OFFICIAL] "

    return " [PHONE_OTHER] "


# ============================================================
# 7. 모델 입력용 전처리
# ============================================================

def preprocess_for_model(text: object) -> str:
    """
    실제 데이터와 합성 데이터 모두 반드시 이 함수를 사용한다.
    """
    if text is None:
        return ""

    value = unicodedata.normalize("NFKC", str(text))

    value = value.replace("\r", " ")
    value = value.replace("\n", " ")
    value = value.replace("\t", " ")

    # URL을 먼저 처리해야 전화번호 정규식과 충돌이 적다.
    value = URL_PATTERN.sub(
        lambda match: classify_url(match.group(0)),
        value,
    )

    value = PHONE_PATTERN.sub(
        lambda match: classify_phone(match.group(0)),
        value,
    )

    value = re.sub(r"\s+", " ", value).strip()

    return value


# ============================================================
# 8. 간단 테스트
# ============================================================

if __name__ == "__main__":
    examples = [
        "[한진택배] 배송조회 https://www.hanjin.com/track 문의 1588-0011",
        "[한진택배] 주소 오류 https://bit.ly/test 확인 바랍니다.",
        "[국외발신] 계정 정지 https://fake-delivery.xyz/check +63-1234-5678",
        "엄마 오늘 저녁에 늦게 들어갈 것 같아",
    ]

    for example in examples:
        print("=" * 80)
        print("원문:", example)
        print("전처리:", preprocess_for_model(example))