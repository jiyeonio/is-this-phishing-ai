from __future__ import annotations

from pathlib import Path

import pandas as pd

from ai.src.url_features import build_feature_dataframe


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
    / "url_rule_feature_summary.csv"
)


# ============================================================
# 2. 요약할 특징
# ============================================================

FEATURES_TO_SUMMARIZE = [
    "url_length",
    "host_length",

    # 도메인 전용 특징
    "host_digit_count",
    "host_digit_ratio",
    "host_letter_ratio",
    "host_hyphen_count",
    "max_domain_label_length",

    # URL 구조 특징
    "path_length",
    "query_length",
    "dot_count",
    "hyphen_count",
    "digit_ratio",
    "special_ratio",
    "subdomain_count",

    # 이진 특징
    "has_https",
    "has_ip_address",
    "has_punycode",
    "is_shortener",
    "is_suspicious_tld",

    # 단어·복잡도 특징
    "suspicious_word_count",
    "host_entropy",
    "url_entropy",
]


# ============================================================
# 3. 특징 요약
# ============================================================

def summarize_features(
    feature_df: pd.DataFrame,
    labels: pd.Series,
) -> pd.DataFrame:
    work_df = feature_df.copy()
    work_df["label"] = labels.to_numpy()

    rows: list[dict] = []

    for feature_name in FEATURES_TO_SUMMARIZE:
        if feature_name not in work_df.columns:
            raise ValueError(
                f"특징 컬럼이 없습니다: {feature_name}"
            )

        for label_value, label_name in [
            (0, "NORMAL"),
            (1, "PHISHING"),
        ]:
            values = work_df.loc[
                work_df["label"].eq(label_value),
                feature_name,
            ]

            rows.append(
                {
                    "feature": feature_name,
                    "class": label_name,
                    "count": int(values.count()),
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "p75": float(values.quantile(0.75)),
                    "p90": float(values.quantile(0.90)),
                    "p95": float(values.quantile(0.95)),
                    "max": float(values.max()),
                }
            )

    return pd.DataFrame(rows)


# ============================================================
# 4. 이진 특징 비율 출력
# ============================================================

def print_binary_feature_rates(
    feature_df: pd.DataFrame,
    labels: pd.Series,
) -> None:
    binary_features = [
        "has_https",
        "has_ip_address",
        "has_punycode",
        "is_shortener",
        "is_suspicious_tld",
    ]

    work_df = feature_df.copy()
    work_df["label"] = labels.to_numpy()

    print("\n" + "=" * 80)
    print("이진 규칙 특징 비율")
    print("=" * 80)

    for feature_name in binary_features:
        normal_rate = work_df.loc[
            work_df["label"].eq(0),
            feature_name,
        ].mean()

        phishing_rate = work_df.loc[
            work_df["label"].eq(1),
            feature_name,
        ].mean()

        print(
            f"{feature_name:24s} "
            f"NORMAL={normal_rate:.4f} "
            f"PHISHING={phishing_rate:.4f}"
        )


# ============================================================
# 5. 실행
# ============================================================

def main() -> None:
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(
            f"Train 파일이 없습니다: {TRAIN_PATH}"
        )

    print("=" * 80)
    print("URL 규칙 특징 분포 분석 시작")
    print("=" * 80)

    train_df = pd.read_csv(
        TRAIN_PATH,
        encoding="utf-8-sig",
    )

    required_columns = {
        "url",
        "label",
    }

    missing = required_columns - set(
        train_df.columns
    )

    if missing:
        raise ValueError(
            f"Train 파일 필수 컬럼 누락: {sorted(missing)}"
        )

    print("Train shape:", train_df.shape)

    feature_df = build_feature_dataframe(
        train_df,
        url_column="url",
    )

    labels = train_df["label"].astype(int)

    print("특징 개수:", feature_df.shape[1])

    summary_df = summarize_features(
        feature_df,
        labels,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print_binary_feature_rates(
        feature_df,
        labels,
    )

    print("\n" + "=" * 80)
    print("도메인 전용 연속형 특징 요약")
    print("=" * 80)

    selected_features = [
        "host_length",
        "host_digit_count",
        "host_digit_ratio",
        "host_letter_ratio",
        "host_hyphen_count",
        "max_domain_label_length",
        "subdomain_count",
        "suspicious_word_count",
        "host_entropy",
    ]

    selected_summary = summary_df[
        summary_df["feature"].isin(
            selected_features
        )
    ].copy()

    # 지정한 특징 순서대로 출력되도록 정렬
    selected_summary["feature"] = pd.Categorical(
        selected_summary["feature"],
        categories=selected_features,
        ordered=True,
    )

    selected_summary = selected_summary.sort_values(
        [
            "feature",
            "class",
        ]
    )

    print(
        selected_summary[
            [
                "feature",
                "class",
                "mean",
                "median",
                "p75",
                "p90",
                "p95",
                "max",
            ]
        ].to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print("\n저장 위치:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()