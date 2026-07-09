"""전처리 (계약 ④ pre dict).

preprocess(text, sender) -> pre dict. A(분류기)도 B(규칙·평판·그래프)도 이 키를 씀.
키 하나만 바뀌어도 신호가 통째로 깨지므로 아래 6개 키는 계약으로 고정.

| 키              | 용도                       | 쓰는 사람        |
| pre["masked"]   | URL 가린 텍스트 (분류기 입력) | A               |
| pre["urls"]     | URL 목록                   | B(규칙·평판)     |
| pre["domains"]  | 도메인 목록                 | B(규칙·평판)     |
| pre["tokens"]   | 문구 토큰 (유사도)          | B(평판·그래프)   |
| pre["sender"]   | 발신번호                    | B               |
| pre["norm"]     | 정규화 원문                 | B(키워드)        |

A 트랙 학습 스크립트도 `from ai.preprocess import mask_urls, normalize` 로
같은 마스킹·정규화를 재사용함(서빙·학습 전처리 일치). 두 함수 시그니처 유지.
"""

import re
import unicodedata

# http(s):// 또는 www. 로 시작하는 URL, 그리고 스킴 없는 맨도메인(예: bit.ly/xxx)까지.
_URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+"
    r"|(?<![@\w.])[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9\-]{1,63})+(?:/[^\s<>\"']*)?",
)

# 마스킹 자리표시자 — 분류기가 URL 문자열 자체가 아니라 "URL이 있다"만 보게.
# INTEGRATION.md·스켈레톤 기준 토큰 = [URL] (train-serving 마스킹 일치, 고정).
URL_TOKEN = "[URL]"

_WORD_RE = re.compile(r"[0-9A-Za-z가-힣]+")


def normalize(text: str) -> str:
    """유니코드 정규화(NFKC) + 공백 정리. 원문 의미는 보존."""
    if text is None:
        return ""
    norm = unicodedata.normalize("NFKC", str(text))
    norm = norm.replace("​", "").replace("﻿", "")  # zero-width 제거
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def extract_urls(text: str) -> list[str]:
    """텍스트에서 URL/도메인 후보를 추출 (등장 순서, 중복 제거)."""
    urls: list[str] = []
    for m in _URL_RE.finditer(text or ""):
        u = m.group(0).rstrip(".,);]。")  # 문장부호 꼬리 정리
        if u and u not in urls:
            urls.append(u)
    return urls


def domain_of(url: str) -> str:
    """URL에서 호스트(도메인)만 소문자로 뽑음. 스킴/www/경로 제거."""
    d = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
    d = re.sub(r"^www\.", "", d, flags=re.IGNORECASE)
    d = d.split("/")[0].split("?")[0].split(":")[0]
    return d.lower()


def mask_urls(text: str) -> str:
    """URL을 URL_TOKEN 으로 치환한 텍스트 반환 (분류기 입력용)."""
    return _URL_RE.sub(URL_TOKEN, text or "")


def tokenize(text: str) -> list[str]:
    """유사도·그래프용 토큰. 숫자/영문/한글 단어 단위."""
    return _WORD_RE.findall(text or "")


def preprocess(text: str, sender: str | None = None) -> dict:
    """계약 ④ pre dict 생성. 모든 하위 신호가 이 dict를 입력으로 받음."""
    norm = normalize(text)
    urls = extract_urls(norm)
    domains: list[str] = []
    for u in urls:
        d = domain_of(u)
        if d and d not in domains:
            domains.append(d)

    return {
        "masked": mask_urls(norm),
        "urls": urls,
        "domains": domains,
        "tokens": tokenize(mask_urls(norm)),
        "sender": (sender or "").strip() or None,
        "norm": norm,
    }
