from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_ROOT
    / "ai"
    / "data"
    / "raw"
    / "kisa_phishing_urls.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "backend"
    / "seed"
    / "phishing_urls.txt"
)


def ensure_scheme(value: object) -> str:
    text = str(value).strip().lower()

    if not text:
        return ""

    if "://" not in text:
        text = "http://" + text

    return text


def extract_domain(value: object) -> str:
    text = ensure_scheme(value)

    if not text:
        return ""

    # userinfo(@)가 포함된 비정상 URL은 정상 도메인 오탐 가능성이 있어 제외
    if "@" in text:
        return ""

    try:
        parsed = urlparse(text)
        domain = parsed.hostname or ""
    except ValueError:
        return ""

    domain = domain.strip().lower()
    domain = domain.removeprefix("www.")
    domain = domain.strip(".")

    return domain


def is_valid_domain(domain: str) -> bool:
    if not domain:
        return False

    if "." not in domain:
        return False

    if len(domain) > 253:
        return False

    allowed = set(
        "abcdefghijklmnopqrstuvwxyz"
        "0123456789-."
    )

    if any(
        character not in allowed
        for character in domain
    ):
        return False

    labels = domain.split(".")

    if any(
        not label
        or len(label) > 63
        or label.startswith("-")
        or label.endswith("-")
        for label in labels
    ):
        return False

    return True


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"KISA 파일이 없습니다: {INPUT_PATH}"
        )

    df = pd.read_csv(
        INPUT_PATH,
        encoding="utf-8-sig",
    )

    if "홈페이지주소" not in df.columns:
        raise ValueError(
            "KISA 파일에 '홈페이지주소' 컬럼이 없습니다."
        )

    domains = (
        df["홈페이지주소"]
        .map(extract_domain)
    )

    valid_domains = sorted(
        {
            domain
            for domain in domains
            if is_valid_domain(domain)
        }
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            "# KISA 피싱 URL 데이터에서 추출한 도메인 명단\n"
        )
        file.write(
            "# 한 줄에 도메인 하나, 중복 제거 완료\n"
        )

        for domain in valid_domains:
            file.write(domain + "\n")

    print("=" * 80)
    print("피싱 도메인 블록리스트 생성 완료")
    print("=" * 80)

    print("원본 행 수:", len(df))
    print("유효 고유 도메인 수:", len(valid_domains))
    print("저장 위치:", OUTPUT_PATH)

    print("\n상위 10개 도메인")
    for domain in valid_domains[:10]:
        print(domain)


if __name__ == "__main__":
    main()