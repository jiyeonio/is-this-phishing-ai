from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


# ============================================================
# 1. 경로 설정
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PREDICTION_PATH = (
    PROJECT_ROOT
    / "ai"
    / "results"
    / "url_rule_validation_predictions.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ai"
    / "results"
    / "url_rule_validation_errors.csv"
)

THRESHOLD = 0.20


# ============================================================
# 2. URL 구조 보조 함수
# ============================================================

def ensure_scheme(value: object) -> str:
    text = str(value).strip().lower()

    if not text:
        return ""

    if "://" not in text:
        text = "http://" + text

    return text


def extract_url_parts(value: object) -> dict[str, object]:
    text = ensure_scheme(value)

    try:
        parsed = urlparse(text)
    except ValueError:
        return {
            "scheme": "",
            "host": "",
            "path": "",
            "query": "",
            "tld": "",
        }

    host = (
        parsed.hostname
        or ""
    ).lower().removeprefix("www.")

    parts = [
        part
        for part in host.split(".")
        if part
    ]

    tld = (
        parts[-1]
        if parts
        else ""
    )

    return {
        "scheme": parsed.scheme or "",
        "host": host,
        "path": parsed.path or "",
        "query": parsed.query or "",
        "tld": tld,
    }


# ============================================================
# 3. 오분류 요약 출력
# ============================================================

def print_error_summary(
    false_positive: pd.DataFrame,
    false_negative: pd.DataFrame,
) -> None:
    print("\n" + "=" * 80)
    print("오분류 개수")
    print("=" * 80)

    print("False Positive:", len(false_positive))
    print("False Negative:", len(false_negative))

    print("\nFalse Positive 규칙 근거 빈도")
    print(
        false_positive["rule_reasons"]
        .fillna("")
        .value_counts()
        .head(20)
        .to_string()
    )

    print("\nFalse Negative TLD 상위 20개")
    print(
        false_negative["tld"]
        .fillna("")
        .value_counts()
        .head(20)
        .to_string()
    )

    print("\nFalse Negative 도메인 상위 30개")
    print(
        false_negative[
            [
                "url",
                "domain",
                "tld",
                "rule_score",
                "rule_reasons",
            ]
        ]
        .head(30)
        .to_string(index=False)
    )

    print("\nFalse Positive 정상 URL 상위 30개")
    print(
        false_positive[
            [
                "url",
                "domain",
                "tld",
                "rule_score",
                "rule_reasons",
            ]
        ]
        .head(30)
        .to_string(index=False)
    )


# ============================================================
# 4. 실행
# ============================================================

def main() -> None:
    if not PREDICTION_PATH.exists():
        raise FileNotFoundError(
            f"예측 결과 파일이 없습니다: {PREDICTION_PATH}"
        )

    print("=" * 80)
    print("URL 구조 규칙 Validation 오분류 분석")
    print("=" * 80)

    df = pd.read_csv(
        PREDICTION_PATH,
        encoding="utf-8-sig",
    )

    required_columns = {
        "url",
        "domain",
        "label",
        "rule_score",
        "rule_reasons",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"필수 컬럼 누락: {sorted(missing)}"
        )

    df = df.copy()

    df["predicted_label"] = (
        df["rule_score"]
        .ge(THRESHOLD)
        .astype(int)
    )

    url_parts = (
        df["url"]
        .map(extract_url_parts)
        .apply(pd.Series)
    )

    df = pd.concat(
        [
            df,
            url_parts,
        ],
        axis=1,
    )

    false_positive = (
        df[
            df["label"].eq(0)
            & df["predicted_label"].eq(1)
        ]
        .sort_values(
            "rule_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    false_negative = (
        df[
            df["label"].eq(1)
            & df["predicted_label"].eq(0)
        ]
        .sort_values(
            [
                "tld",
                "domain",
            ]
        )
        .reset_index(drop=True)
    )

    false_positive["error_type"] = (
        "FALSE_POSITIVE"
    )

    false_negative["error_type"] = (
        "FALSE_NEGATIVE"
    )

    error_df = pd.concat(
        [
            false_positive,
            false_negative,
        ],
        ignore_index=True,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    error_df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("Validation 전체 행 수:", len(df))
    print("사용 임계값:", THRESHOLD)

    print_error_summary(
        false_positive,
        false_negative,
    )

    print("\n오분류 전체 저장 위치:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()