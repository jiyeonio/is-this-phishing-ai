from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from ai.url_rule_engine import (
    URL_RULE_THRESHOLD,
    analyze_url,
)


# ============================================================
# 1. 경로 설정
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_PATH = (
    PROJECT_ROOT
    / "ai"
    / "data"
    / "processed"
    / "url_test.csv"
)

RESULT_DIR = (
    PROJECT_ROOT
    / "ai"
    / "results"
)

PREDICTION_PATH = (
    RESULT_DIR
    / "url_rule_test_predictions.csv"
)

METRICS_PATH = (
    RESULT_DIR
    / "url_rule_test_metrics.json"
)


# ============================================================
# 2. 실행
# ============================================================

def main() -> None:
    if not TEST_PATH.exists():
        raise FileNotFoundError(
            f"Test 파일이 없습니다: {TEST_PATH}"
        )

    print("=" * 80)
    print("URL 구조 규칙 Test 최종평가")
    print("=" * 80)

    test_df = pd.read_csv(
        TEST_PATH,
        encoding="utf-8-sig",
    )

    required_columns = {
        "url",
        "domain",
        "label",
        "source",
    }

    missing = required_columns - set(
        test_df.columns
    )

    if missing:
        raise ValueError(
            f"Test 파일 필수 컬럼 누락: {sorted(missing)}"
        )

    labels = (
        test_df["label"]
        .astype(int)
        .to_numpy()
    )

    results = [
        analyze_url(str(url))
        for url in test_df["url"]
    ]

    scores = np.array(
        [
            result[0]
            for result in results
        ],
        dtype=float,
    )

    evidence_texts = [
        " | ".join(
            f"{item['type']}: {item['detail']}"
            for item in result[1]
        )
        for result in results
    ]

    predictions = (
        scores >= URL_RULE_THRESHOLD
    ).astype(int)

    accuracy = accuracy_score(
        labels,
        predictions,
    )

    precision = precision_score(
        labels,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        labels,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        labels,
        predictions,
        zero_division=0,
    )

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

    print("Test shape:", test_df.shape)
    print("확정 임계값:", URL_RULE_THRESHOLD)

    print("\n" + "=" * 80)
    print("최종 Test 성능")
    print("=" * 80)

    print(f"Accuracy : {accuracy:.6f}")
    print(f"Precision: {precision:.6f}")
    print(f"Recall   : {recall:.6f}")
    print(f"F1       : {f1:.6f}")

    print("\nConfusion Matrix")
    print(f"TN {tn} / FP {fp}")
    print(f"FN {fn} / TP {tp}")

    print("\nClassification Report")
    print(
        classification_report(
            labels,
            predictions,
            target_names=[
                "NORMAL",
                "PHISHING",
            ],
            digits=4,
            zero_division=0,
        )
    )

    prediction_df = test_df[
        [
            "url",
            "domain",
            "label",
            "source",
        ]
    ].copy()

    prediction_df["rule_score"] = scores
    prediction_df["predicted_label"] = predictions
    prediction_df["correct"] = (
        prediction_df["label"]
        == prediction_df["predicted_label"]
    )
    prediction_df["rule_evidence"] = evidence_texts

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    prediction_df.to_csv(
        PREDICTION_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    metrics = {
        "engine": "rule_based_url_structure",
        "blocklist_used": False,
        "threshold": float(
            URL_RULE_THRESHOLD
        ),
        "test_rows": int(
            len(test_df)
        ),
        "accuracy": float(
            accuracy
        ),
        "precision": float(
            precision
        ),
        "recall": float(
            recall
        ),
        "f1": float(
            f1
        ),
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
        },
    }

    with METRICS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n저장 위치")
    print(PREDICTION_PATH)
    print(METRICS_PATH)

    print(
        "\n주의: Test 결과를 확인한 뒤 "
        "규칙·가중치·임계값을 다시 조정하지 않습니다."
    )


if __name__ == "__main__":
    main()