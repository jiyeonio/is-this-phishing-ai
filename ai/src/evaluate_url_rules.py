from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from ai.src.url_features import build_feature_dataframe


# ============================================================
# 1. 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VALIDATION_PATH = (
    PROJECT_ROOT
    / "ai"
    / "data"
    / "processed"
    / "url_validation.csv"
)

RESULT_DIR = (
    PROJECT_ROOT
    / "ai"
    / "results"
)

PREDICTION_PATH = (
    RESULT_DIR
    / "url_rule_validation_predictions.csv"
)

METRICS_PATH = (
    RESULT_DIR
    / "url_rule_validation_thresholds.csv"
)


# ============================================================
# 2. 후보 구조 규칙 점수
# ============================================================

def calculate_rule_score(
    feature_row: pd.Series,
) -> tuple[float, list[str]]:
    """
    블록리스트를 사용하지 않고 URL 구조만으로 점수를 계산한다.

    Train 데이터 분석 결과와 일반적인 URL 위장 신호를 바탕으로 만든
    1차 후보 규칙이며, Validation 결과를 보고 조정한다.
    """
    score = 0.0
    reasons: list[str] = []

    # 강한 구조 신호
    if feature_row["has_ip_address"] >= 1:
        score += 0.30
        reasons.append("IP 주소 직접 사용")

    if feature_row["is_shortener"] >= 1:
        score += 0.25
        reasons.append("단축 URL 사용")

    if feature_row["is_suspicious_tld"] >= 1:
        score += 0.20
        reasons.append("의심 TLD 사용")

    if feature_row["has_punycode"] >= 1:
        score += 0.20
        reasons.append("Punycode 사용")

    # 중간·약한 구조 신호
    if feature_row["host_digit_ratio"] >= 0.20:
        score += 0.15
        reasons.append("도메인 숫자 비율 20% 이상")
    elif feature_row["host_digit_ratio"] >= 0.10:
        score += 0.08
        reasons.append("도메인 숫자 비율 10% 이상")

    if feature_row["subdomain_count"] >= 3:
        score += 0.15
        reasons.append("서브도메인 3개 이상")
    elif feature_row["subdomain_count"] >= 2:
        score += 0.08
        reasons.append("서브도메인 2개 이상")

    if feature_row["at_count"] >= 1:
        score += 0.25
        reasons.append("@ 문자로 주소 은폐 가능")

    return round(min(score, 1.0), 4), reasons


# ============================================================
# 3. 임계값별 평가
# ============================================================

def evaluate_thresholds(
    labels: pd.Series,
    scores: np.ndarray,
) -> pd.DataFrame:
    thresholds = [
        0.08,
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.35,
        0.40,
        0.50,
    ]

    rows: list[dict] = []

    for threshold in thresholds:
        predictions = (
            scores >= threshold
        ).astype(int)

        matrix = confusion_matrix(
            labels,
            predictions,
            labels=[0, 1],
        )

        tn, fp, fn, tp = (
            int(matrix[0, 0]),
            int(matrix[0, 1]),
            int(matrix[1, 0]),
            int(matrix[1, 1]),
        )

        rows.append(
            {
                "threshold": threshold,
                "accuracy": accuracy_score(
                    labels,
                    predictions,
                ),
                "precision": precision_score(
                    labels,
                    predictions,
                    zero_division=0,
                ),
                "recall": recall_score(
                    labels,
                    predictions,
                    zero_division=0,
                ),
                "f1": f1_score(
                    labels,
                    predictions,
                    zero_division=0,
                ),
                "tn": tn,
                "fp": fp,
                "fn": fn,
                "tp": tp,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 4. 규칙별 탐지 비율
# ============================================================

def print_rule_rates(
    feature_df: pd.DataFrame,
    labels: pd.Series,
) -> None:
    work_df = feature_df.copy()
    work_df["label"] = labels.to_numpy()

    conditions = {
        "IP 주소 직접 사용":
            work_df["has_ip_address"].ge(1),

        "단축 URL":
            work_df["is_shortener"].ge(1),

        "의심 TLD":
            work_df["is_suspicious_tld"].ge(1),

        "Punycode":
            work_df["has_punycode"].ge(1),

        "도메인 숫자 비율 >= 0.10":
            work_df["host_digit_ratio"].ge(0.10),

        "도메인 숫자 비율 >= 0.20":
            work_df["host_digit_ratio"].ge(0.20),

        "서브도메인 >= 2":
            work_df["subdomain_count"].ge(2),

        "@ 문자 포함":
            work_df["at_count"].ge(1),
    }

    print("\n" + "=" * 80)
    print("Validation 규칙별 발생 비율")
    print("=" * 80)

    for rule_name, condition in conditions.items():
        normal_rate = condition[
            work_df["label"].eq(0)
        ].mean()

        phishing_rate = condition[
            work_df["label"].eq(1)
        ].mean()

        print(
            f"{rule_name:28s} "
            f"NORMAL={normal_rate:.4f} "
            f"PHISHING={phishing_rate:.4f}"
        )


# ============================================================
# 5. 실행
# ============================================================

def main() -> None:
    if not VALIDATION_PATH.exists():
        raise FileNotFoundError(
            f"Validation 파일이 없습니다: {VALIDATION_PATH}"
        )

    print("=" * 80)
    print("URL 구조 규칙 Validation 평가")
    print("=" * 80)

    validation_df = pd.read_csv(
        VALIDATION_PATH,
        encoding="utf-8-sig",
    )

    labels = (
        validation_df["label"]
        .astype(int)
    )

    feature_df = build_feature_dataframe(
        validation_df,
        url_column="url",
    )

    print("Validation shape:", validation_df.shape)
    print("특징 개수:", feature_df.shape[1])

    print_rule_rates(
        feature_df,
        labels,
    )

    results = [
        calculate_rule_score(row)
        for _, row in feature_df.iterrows()
    ]

    scores = np.array(
        [
            result[0]
            for result in results
        ],
        dtype=float,
    )

    reasons = [
        " | ".join(result[1])
        for result in results
    ]

    metrics_df = evaluate_thresholds(
        labels,
        scores,
    )

    print("\n" + "=" * 80)
    print("임계값별 성능")
    print("=" * 80)

    print(
        metrics_df.to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    prediction_df = validation_df[
        [
            "url",
            "domain",
            "label",
            "source",
        ]
    ].copy()

    prediction_df["rule_score"] = scores
    prediction_df["rule_reasons"] = reasons

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    prediction_df.to_csv(
        PREDICTION_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    metrics_df.to_csv(
        METRICS_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n저장 위치")
    print(PREDICTION_PATH)
    print(METRICS_PATH)


if __name__ == "__main__":
    main()