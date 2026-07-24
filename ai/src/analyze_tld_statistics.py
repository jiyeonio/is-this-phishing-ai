from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


# ============================================================
# 1. 경로 설정
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAIN_PATH = (
    PROJECT_ROOT
    / "ai"
    / "data"
    / "processed"
    / "url_train.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ai"
    / "results"
    / "url_train_tld_statistics.csv"
)


# ============================================================
# 2. URL 파싱
# ============================================================

def ensure_scheme(value: object) -> str:
    text = str(value).strip().lower()

    if not text:
        return ""

    if "://" not in text:
        text = "http://" + text

    return text


def extract_tld(value: object) -> str:
    text = ensure_scheme(value)

    if not text:
        return ""

    try:
        parsed = urlparse(text)
        host = (
            parsed.hostname
            or ""
        ).lower().removeprefix("www.")
    except ValueError:
        return ""

    parts = [
        part
        for part in host.split(".")
        if part
    ]

    if len(parts) < 2:
        return ""

    return parts[-1]


# ============================================================
# 3. TLD 통계 생성
# ============================================================

def build_tld_statistics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    work_df = df.copy()

    work_df["tld"] = (
        work_df["url"]
        .map(extract_tld)
    )

    work_df = work_df[
        work_df["tld"].ne("")
    ].copy()

    normal_counts = (
        work_df[
            work_df["label"].eq(0)
        ]
        .groupby("tld")
        .size()
        .rename("normal_count")
    )

    phishing_counts = (
        work_df[
            work_df["label"].eq(1)
        ]
        .groupby("tld")
        .size()
        .rename("phishing_count")
    )

    statistics = (
        pd.concat(
            [
                normal_counts,
                phishing_counts,
            ],
            axis=1,
        )
        .fillna(0)
        .reset_index()
    )

    statistics["normal_count"] = (
        statistics["normal_count"]
        .astype(int)
    )

    statistics["phishing_count"] = (
        statistics["phishing_count"]
        .astype(int)
    )

    statistics["total_count"] = (
        statistics["normal_count"]
        + statistics["phishing_count"]
    )

    statistics["phishing_rate"] = (
        statistics["phishing_count"]
        / statistics["total_count"]
    )

    # 표본이 너무 작은 TLD를 바로 채택하지 않기 위한 후보 기준
    statistics["candidate_rule"] = (
        statistics["phishing_count"].ge(20)
        & statistics["phishing_rate"].ge(0.90)
    )

    statistics = statistics.sort_values(
        [
            "candidate_rule",
            "phishing_count",
            "phishing_rate",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    ).reset_index(drop=True)

    return statistics


# ============================================================
# 4. 실행
# ============================================================

def main() -> None:
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(
            f"Train 파일이 없습니다: {TRAIN_PATH}"
        )

    print("=" * 80)
    print("Train 데이터 TLD 통계 분석")
    print("=" * 80)

    train_df = pd.read_csv(
        TRAIN_PATH,
        encoding="utf-8-sig",
    )

    required_columns = {
        "url",
        "label",
    }

    missing = (
        required_columns
        - set(train_df.columns)
    )

    if missing:
        raise ValueError(
            f"필수 컬럼 누락: {sorted(missing)}"
        )

    train_df["label"] = (
        train_df["label"]
        .astype(int)
    )

    statistics = build_tld_statistics(
        train_df
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    statistics.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    candidates = statistics[
        statistics["candidate_rule"]
    ].copy()

    print("Train 전체 행 수:", len(train_df))
    print("전체 TLD 종류:", len(statistics))
    print("의심 TLD 후보 수:", len(candidates))

    print("\n피싱 수가 많은 TLD 상위 30개")
    print(
        statistics[
            [
                "tld",
                "normal_count",
                "phishing_count",
                "total_count",
                "phishing_rate",
                "candidate_rule",
            ]
        ]
        .sort_values(
            "phishing_count",
            ascending=False,
        )
        .head(30)
        .to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print("\n의심 TLD 후보 전체")
    print(
        candidates[
            [
                "tld",
                "normal_count",
                "phishing_count",
                "total_count",
                "phishing_rate",
            ]
        ]
        .to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print("\n저장 위치:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()