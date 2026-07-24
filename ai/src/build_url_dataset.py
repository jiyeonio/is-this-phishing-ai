from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


# ============================================================
# 1. 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

KISA_PATH = RAW_DIR / "kisa_phishing_urls.csv"
TOP1M_PATH = RAW_DIR / "top_1m_domains.csv"

OUTPUT_PATH = PROCESSED_DIR / "url_dataset.csv"

# 처음에는 정상/피싱 각각 30,000개만 사용
NORMAL_SAMPLE_SIZE = 30_000
PHISHING_SAMPLE_SIZE = 30_000

SEED = 42

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 2. URL 정리 함수
# ============================================================

def normalize_url(value: object) -> str:
    """
    URL 또는 도메인을 소문자 형태로 정리한다.
    프로토콜이 없으면 임시로 http://를 붙여 파싱한다.
    """
    if value is None:
        return ""

    text = str(value).strip().lower()

    if not text:
        return ""

    text = text.replace(" ", "")

    if not re.match(r"^https?://", text):
        text = "http://" + text

    return text


def extract_domain(value: object) -> str:
    """
    URL에서 hostname만 추출한다.
    """
    normalized = normalize_url(value)

    if not normalized:
        return ""

    try:
        parsed = urlparse(normalized)
        domain = parsed.hostname or ""
    except ValueError:
        return ""

    domain = domain.lower()
    domain = domain.removeprefix("www.")
    domain = domain.strip(".")

    return domain


def is_valid_domain(domain: str) -> bool:
    """
    최소한의 도메인 형식 검증.
    """
    if not domain:
        return False

    if len(domain) > 253:
        return False

    if "." not in domain:
        return False

    pattern = re.compile(
        r"^[a-z0-9.-]+$",
        flags=re.IGNORECASE,
    )

    if not pattern.fullmatch(domain):
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


# ============================================================
# 3. KISA 피싱 데이터 읽기
# ============================================================

def load_phishing_data() -> pd.DataFrame:
    df = pd.read_csv(
        KISA_PATH,
        encoding="utf-8-sig",
    )

    required_columns = {
        "날짜",
        "홈페이지주소",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"KISA 파일 필수 컬럼 누락: {sorted(missing)}"
        )

    phishing_df = pd.DataFrame(
        {
            "raw_url": df["홈페이지주소"],
            "date": df["날짜"],
        }
    )

    phishing_df["url"] = (
        phishing_df["raw_url"]
        .map(normalize_url)
    )

    phishing_df["domain"] = (
        phishing_df["raw_url"]
        .map(extract_domain)
    )

    phishing_df = phishing_df[
        phishing_df["domain"]
        .map(is_valid_domain)
    ].copy()

    phishing_df = (
        phishing_df
        .drop_duplicates(
            subset=["url"]
        )
        .reset_index(drop=True)
    )

    phishing_df["label"] = 1
    phishing_df["source"] = "kisa_phishing"

    return phishing_df[
        [
            "url",
            "domain",
            "label",
            "source",
            "date",
        ]
    ]


# ============================================================
# 4. Top-1M 정상 후보 읽기
# ============================================================

def load_normal_data() -> pd.DataFrame:
    df = pd.read_csv(
        TOP1M_PATH,
        header=None,
        names=[
            "rank",
            "raw_domain",
        ],
    )

    normal_df = pd.DataFrame(
        {
            "rank": df["rank"],
            "raw_url": df["raw_domain"],
        }
    )

    normal_df["url"] = (
        normal_df["raw_url"]
        .map(normalize_url)
    )

    normal_df["domain"] = (
        normal_df["raw_url"]
        .map(extract_domain)
    )

    normal_df = normal_df[
        normal_df["domain"]
        .map(is_valid_domain)
    ].copy()

    normal_df = (
        normal_df
        .drop_duplicates(
            subset=["domain"]
        )
        .sort_values("rank")
        .reset_index(drop=True)
    )

    normal_df["label"] = 0
    normal_df["source"] = "top1m_normal"
    normal_df["date"] = pd.NA

    return normal_df[
        [
            "url",
            "domain",
            "label",
            "source",
            "date",
            "rank",
        ]
    ]


# ============================================================
# 5. 정상/피싱 결합
# ============================================================

def main() -> None:
    if not KISA_PATH.exists():
        raise FileNotFoundError(
            f"KISA 파일이 없습니다: {KISA_PATH}"
        )

    if not TOP1M_PATH.exists():
        raise FileNotFoundError(
            f"Top-1M 파일이 없습니다: {TOP1M_PATH}"
        )

    print("=" * 80)
    print("URL 데이터셋 생성 시작")
    print("=" * 80)

    phishing_df = load_phishing_data()
    normal_df = load_normal_data()

    print("\n정제 후 피싱 URL 수:", len(phishing_df))
    print("정제 후 정상 후보 수:", len(normal_df))

    # KISA 피싱 도메인과 겹치는 정상 후보 제거
    phishing_domains = set(
        phishing_df["domain"]
    )

    overlap_count = int(
        normal_df["domain"]
        .isin(phishing_domains)
        .sum()
    )

    print(
        "정상 후보 중 KISA 피싱 도메인과 겹치는 수:",
        overlap_count,
    )

    normal_df = normal_df[
        ~normal_df["domain"]
        .isin(phishing_domains)
    ].copy()

    # 피싱은 랜덤 샘플링
    phishing_sample_size = min(
        PHISHING_SAMPLE_SIZE,
        len(phishing_df),
    )

    phishing_sample = (
        phishing_df
        .sample(
            n=phishing_sample_size,
            random_state=SEED,
        )
        .reset_index(drop=True)
    )

    # 정상은 인기 순위 상위에서 선택
    normal_sample_size = min(
        NORMAL_SAMPLE_SIZE,
        len(normal_df),
    )

    normal_sample = (
        normal_df
        .head(normal_sample_size)
        .reset_index(drop=True)
    )

    all_columns = [
        "url",
        "domain",
        "label",
        "source",
        "date",
        "rank",
    ]

    phishing_sample = (
        phishing_sample
        .reindex(columns=all_columns)
    )

    normal_sample = (
        normal_sample
        .reindex(columns=all_columns)
    )

    dataset = pd.concat(
        [
            normal_sample,
            phishing_sample,
        ],
        ignore_index=True,
    )

    dataset = (
        dataset
        .sample(
            frac=1,
            random_state=SEED,
        )
        .reset_index(drop=True)
    )

    dataset.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 80)
    print("URL 데이터셋 생성 완료")
    print("=" * 80)

    print("\n최종 shape:", dataset.shape)

    print("\n라벨 분포")
    print(
        dataset["label"]
        .value_counts()
        .sort_index()
    )

    print("\n출처 분포")
    print(
        dataset["source"]
        .value_counts()
    )

    print("\n중복 URL 수:")
    print(
        dataset["url"]
        .duplicated()
        .sum()
    )

    print("\n중복 도메인 수:")
    print(
        dataset["domain"]
        .duplicated()
        .sum()
    )

    print("\n저장 위치:")
    print(OUTPUT_PATH)

    print("\n정상 URL 예시")
    print(
        dataset[
            dataset["label"].eq(0)
        ]
        .head(5)
        [
            [
                "url",
                "domain",
                "label",
            ]
        ]
        .to_string(index=False)
    )

    print("\n피싱 URL 예시")
    print(
        dataset[
            dataset["label"].eq(1)
        ]
        .head(5)
        [
            [
                "url",
                "domain",
                "label",
            ]
        ]
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()