"""전처리 (계약 ④ pre dict).

preprocess(text, sender) -> pre dict. A(분류기)도 B(규칙·평판·그래프)도 이 키를 씀.
키 하나만 바뀌어도 신호가 통째로 깨지므로 아래 6개 키는 계약으로 고정.

| 키              | 용도                         | 쓰는 사람        |
| pre["masked"]    | URL 가린 텍스트 (분류기 입력) | A               |
| pre["urls"]      | URL 목록                     | B(규칙·평판)     |
| pre["domains"]   | 도메인 목록                  | B(규칙·평판)     |
| pre["tokens"]    | 문구 토큰 (유사도)           | B(평판·그래프)   |
| pre["sender"]    | 발신번호                     | B               |
| pre["norm"]      | 정규화 원문                  | B(키워드)        |

중요:
- normalize(), mask_urls()의 기존 동작과 시그니처는 유지한다.
- 저장된 텍스트 분류모델과의 train-serving 전처리 일치를 깨지 않는다.
- 난독화·줄바꿈 URL 복원은 rules용 urls/domains 추출에만 적용한다.
"""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlparse


# ============================================================
# 1. 기존 분류기 마스킹용 URL 정규식
# ============================================================

# 이 정규식은 기존 학습·서빙 마스킹 일치를 위해 유지한다.
_MASK_URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+"
    r"|(?<![@\w.])[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9\-]{1,63})+(?:/[^\s<>\"']*)?",
)


# ============================================================
# 2. rules용 보완 URL 추출 정규식
# ============================================================

# 한글 바로 뒤에 붙은 asq.kr 같은 주소도 추출한다.
# 영문·숫자·@ 바로 뒤에서 중간 문자열을 잘못 자르는 것만 방지한다.
_EXTRACT_URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+"
    r"|(?<![A-Za-z0-9@])"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9\-]{1,63})+"
    r"(?::\d{1,5})?"
    r"(?:/[^\s<>\"']*)?",
    flags=re.IGNORECASE,
)


URL_TOKEN = "[URL]"

_WORD_RE = re.compile(
    r"[0-9A-Za-z가-힣]+"
)

_TRAILING_URL_PUNCTUATION = (
    ".,);]}>。,"
)


# ============================================================
# 3. 기본 정규화
# ============================================================

def normalize(text: str) -> str:
    """유니코드 정규화(NFKC) + 공백 정리. 원문 의미는 보존."""
    if text is None:
        return ""

    norm = unicodedata.normalize(
        "NFKC",
        str(text),
    )

    norm = (
        norm
        .replace("\u200b", "")
        .replace("\ufeff", "")
    )

    norm = re.sub(
        r"\s+",
        " ",
        norm,
    ).strip()

    return norm


# ============================================================
# 4. URL 추출 전용 보완
# ============================================================

def _normalize_for_url_scan(
    text: str,
) -> str:
    """
    rules용 URL 추출에만 사용하는 보완 문자열을 만든다.

    처리:
    - NFKC로 ⓔ, ⓞ, ② 등의 호환문자를 일반 문자로 변환
    - zero-width 문자 제거
    - https:// 뒤 줄바꿈 제거
    - URL 내부 줄바꿈을 제한적으로 연결
    - 관찰된 bit/ly 형태를 bit.ly로 제한적 복원

    분류기 입력인 masked에는 이 문자열을 사용하지 않는다.
    """
    if text is None:
        return ""

    scan_text = unicodedata.normalize(
        "NFKC",
        str(text),
    )

    scan_text = (
        scan_text
        .replace("\u200b", "")
        .replace("\ufeff", "")
    )

    # https:// 다음에 삽입된 줄바꿈·공백 제거
    scan_text = re.sub(
        r"(?i)\b(https?://)\s+",
        r"\1",
        scan_text,
    )

    # 스킴 URL 내부에서 줄바꿈으로 분리된 ASCII URL 조각 연결
    # 예:
    # https://play.google.com/
    # store/apps/ → https://play.google.com/store/apps/
    url_chars = r"A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%\-"

    for _ in range(5):
        repaired = re.sub(
            rf"(?i)(https?://[{url_chars}]*)"
            rf"[\r\n\t ]+"
            rf"(?=[{url_chars}])",
            r"\1",
            scan_text,
        )

        if repaired == scan_text:
            break

        scan_text = repaired

    # 실제 실패 사례에서 관찰된 제한적 복원
    scan_text = re.sub(
        r"(?i)\bbit\s*/\s*ly\b",
        "bit.ly",
        scan_text,
    )

    return scan_text


# ============================================================
# 5. URL 및 도메인 추출
# ============================================================

def extract_urls(text: str) -> list[str]:
    """
    텍스트에서 URL·도메인 후보를 추출한다.

    - 등장 순서 유지
    - 중복 제거
    - rules용 보완 문자열에서 추출
    """
    scan_text = _normalize_for_url_scan(
        text,
    )

    urls: list[str] = []

    for match in _EXTRACT_URL_RE.finditer(
        scan_text
    ):
        url = (
            match.group(0)
            .rstrip(
                _TRAILING_URL_PUNCTUATION
            )
        )

        if url and url not in urls:
            urls.append(url)

    return urls


def domain_of(url: str) -> str:
    """
    URL에서 호스트를 소문자로 추출한다.

    포트·경로·쿼리를 제외하고 www. 접두어를 제거한다.
    """
    value = str(url).strip()

    if not value:
        return ""

    parse_value = value

    if not re.match(
        r"^[a-z][a-z0-9+.-]*://",
        parse_value,
        flags=re.IGNORECASE,
    ):
        parse_value = (
            "http://" + parse_value
        )

    try:
        parsed = urlparse(
            parse_value
        )
        domain = (
            parsed.hostname
            or ""
        )
    except ValueError:
        return ""

    domain = (
        domain
        .strip()
        .lower()
        .removeprefix("www.")
        .strip(".")
    )

    return domain


# ============================================================
# 6. 분류기용 마스킹·토큰화
# ============================================================

def mask_urls(text: str) -> str:
    """
    URL을 URL_TOKEN으로 치환한다.

    기존 텍스트 모델 학습·서빙 일치를 위해 기존 마스킹 정규식을 사용한다.
    """
    return _MASK_URL_RE.sub(
        URL_TOKEN,
        text or "",
    )


def tokenize(text: str) -> list[str]:
    """유사도·그래프용 토큰. 숫자/영문/한글 단어 단위."""
    return _WORD_RE.findall(
        text or ""
    )


# ============================================================
# 7. 계약 pre dict 생성
# ============================================================

def preprocess(
    text: str,
    sender: str | None = None,
) -> dict:
    """계약 ④ pre dict 생성. 반환 키 6개는 고정한다."""
    norm = normalize(text)

    # URL 추출에는 줄바꿈·난독화 보완 전용 처리를 적용
    urls = extract_urls(text)

    domains: list[str] = []

    for url in urls:
        domain = domain_of(url)

        if (
            domain
            and domain not in domains
        ):
            domains.append(domain)

    # 분류기 입력은 기존 정규화·마스킹 방식을 유지
    masked = mask_urls(norm)

    return {
        "masked": masked,
        "urls": urls,
        "domains": domains,
        "tokens": tokenize(masked),
        "sender": (
            (sender or "").strip()
            or None
        ),
        "norm": norm,
    }