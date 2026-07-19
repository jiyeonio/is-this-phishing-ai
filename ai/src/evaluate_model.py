from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from src.text_features import preprocess_for_model


# ============================================================
# 1. 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULT_DIR = PROJECT_ROOT / "results" / "model_comparison"

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 2. 비교할 모델
# ============================================================

MODEL_PATHS = {
    "baseline": (
        PROJECT_ROOT
        / "models"
        / "kcelectra_baseline"
        / "checkpoint-779"
    ), 
    "augmented": (
        PROJECT_ROOT
        / "models"
        / "kcelectra_augmented"
        / "best_model"
    ),
}


# ============================================================
# 3. 평가 데이터
# ============================================================

VALIDATION_PATH = (
    PROCESSED_DIR
    / "validation_real.csv"
)


def find_hard_file() -> Path:
    """
    data/processed 안에서 hard가 포함된 CSV를 찾는다.
    """

    candidates = sorted(
        PROCESSED_DIR.glob("*hard*.csv")
    )

    if not candidates:
        candidates = sorted(
            PROCESSED_DIR.glob("*HARD*.csv")
        )

    if not candidates:
        raise FileNotFoundError(
            "data/processed 안에서 HARD CSV를 찾지 못했습니다.\n"
            "HARD 평가 파일 이름에 hard 또는 HARD가 들어가도록 해주세요."
        )

    print("\n찾은 HARD 파일 후보")

    for path in candidates:
        print("-", path.name)

    # 여러 개면 첫 번째 파일 사용
    return candidates[0]


# ============================================================
# 4. 데이터 읽기
# ============================================================

def read_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"파일을 찾지 못했습니다: {path}"
        )

    df = pd.read_csv(
        path,
        encoding="utf-8-sig",
    )

    print("\n데이터 읽기:", path)
    print("shape:", df.shape)
    print("columns:", df.columns.tolist())

    # label 컬럼 확인
    if "label" not in df.columns:
        raise ValueError(
            f"label 컬럼이 없습니다: {path}"
        )

    df = df.dropna(
        subset=["label"]
    ).copy()

    df["label"] = (
        df["label"]
        .astype(int)
    )

    # text가 없으면 content에서 생성
    if "text" not in df.columns:
        if "content" in df.columns:
            print(
                "text 컬럼이 없어 content에서 전처리합니다."
            )

            df["text"] = (
                df["content"]
                .map(preprocess_for_model)
            )

        else:
            raise ValueError(
                "text와 content 컬럼이 모두 없습니다."
            )

    df = df.dropna(
        subset=["text"]
    ).copy()

    df["text"] = (
        df["text"]
        .astype(str)
    )

    return df.reset_index(drop=True)


# ============================================================
# 5. 모델 예측
# ============================================================

def predict_probabilities(
    model_path: Path,
    df: pd.DataFrame,
    batch_size: int = 16,
) -> np.ndarray:
    if not model_path.exists():
        raise FileNotFoundError(
            f"모델 폴더를 찾지 못했습니다: {model_path}"
        )

    print("\n모델 불러오기:")
    print(model_path)

    tokenizer = AutoTokenizer.from_pretrained(
        model_path
    )

    model = (
        AutoModelForSequenceClassification
        .from_pretrained(model_path)
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    model.to(device)
    model.eval()

    probabilities = []

    for start in range(
        0,
        len(df),
        batch_size,
    ):
        batch_texts = (
            df["text"]
            .iloc[
                start:start + batch_size
            ]
            .tolist()
        )

        encoded = tokenizer(
            batch_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=256,
        )

        encoded = {
            key: value.to(device)
            for key, value in encoded.items()
        }

        with torch.no_grad():
            logits = model(
                **encoded
            ).logits

            batch_probabilities = (
                torch.softmax(
                    logits,
                    dim=1,
                )[:, 1]
                .cpu()
                .numpy()
            )

        probabilities.extend(
            batch_probabilities.tolist()
        )

        if start % 320 == 0:
            print(
                f"예측 진행: "
                f"{min(start + batch_size, len(df))}"
                f"/{len(df)}"
            )

    return np.array(
        probabilities,
        dtype=float,
    )


# ============================================================
# 6. 지표 계산
# ============================================================

def calculate_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    threshold: float = 0.5,
) -> dict:
    predictions = (
        probabilities >= threshold
    ).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        labels,
        predictions,
        labels=[0, 1],
    ).ravel()

    return {
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
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


# ============================================================
# 7. Pair Accuracy
# ============================================================

def calculate_pair_accuracy(
    result_df: pd.DataFrame,
) -> float | None:
    if "pair_id" not in result_df.columns:
        return None

    pair_result = (
        result_df
        .groupby("pair_id")
        .apply(
            lambda group: bool(
                group["is_correct"].all()
            ),
            include_groups=False,
        )
    )

    if len(pair_result) == 0:
        return None

    return float(
        pair_result.mean()
    )


# ============================================================
# 8. 모델 하나 평가
# ============================================================

def evaluate_one(
    model_name: str,
    model_path: Path,
    dataset_name: str,
    dataset_path: Path,
) -> dict:
    print("\n" + "=" * 80)
    print(
        f"{model_name} - {dataset_name} 평가"
    )
    print("=" * 80)

    df = read_dataset(
        dataset_path
    )

    probabilities = predict_probabilities(
        model_path=model_path,
        df=df,
    )

    labels = (
        df["label"]
        .to_numpy()
    )

    metrics = calculate_metrics(
        labels=labels,
        probabilities=probabilities,
        threshold=0.5,
    )

    result_df = df.copy()

    result_df["phishing_probability"] = (
        probabilities
    )

    result_df["predicted_label"] = (
        probabilities >= 0.5
    ).astype(int)

    result_df["is_correct"] = (
        result_df["label"]
        == result_df["predicted_label"]
    )

    pair_accuracy = calculate_pair_accuracy(
        result_df
    )

    metrics["model"] = model_name
    metrics["dataset"] = dataset_name
    metrics["rows"] = len(result_df)
    metrics["pair_accuracy"] = pair_accuracy

    output_path = (
        RESULT_DIR
        / f"{model_name}_{dataset_name}_predictions.csv"
    )

    result_df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n평가 결과")

    for key in [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "tn",
        "fp",
        "fn",
        "tp",
        "pair_accuracy",
    ]:
        print(
            f"{key}: {metrics[key]}"
        )

    print("\n예측 저장:")
    print(output_path)

    return metrics


# ============================================================
# 9. 전체 실행
# ============================================================

def main() -> None:
    print("=" * 80)
    print("Baseline / Augmented 동일 조건 비교")
    print("=" * 80)

    print(
        "장치:",
        "cuda"
        if torch.cuda.is_available()
        else "cpu",
    )

    hard_path = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "korean_phishing_hard_test_1000.csv"
)

    datasets = {
        "validation": VALIDATION_PATH,
        "hard": hard_path,
    }

    all_metrics = []

    for model_name, model_path in (
        MODEL_PATHS.items()
    ):
        if not model_path.exists():
            print("\n경고: 모델이 없어 건너뜁니다.")
            print(model_name, model_path)
            continue

        for dataset_name, dataset_path in (
            datasets.items()
        ):
            metrics = evaluate_one(
                model_name=model_name,
                model_path=model_path,
                dataset_name=dataset_name,
                dataset_path=dataset_path,
            )

            all_metrics.append(
                metrics
            )

    if not all_metrics:
        raise RuntimeError(
            "평가된 모델이 없습니다. "
            "모델 경로를 확인하세요."
        )

    comparison_df = pd.DataFrame(
        all_metrics
    )

    comparison_df = comparison_df[
        [
            "model",
            "dataset",
            "rows",
            "threshold",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "tn",
            "fp",
            "fn",
            "tp",
            "pair_accuracy",
        ]
    ]

    comparison_path = (
        RESULT_DIR
        / "model_comparison.csv"
    )

    comparison_df.to_csv(
        comparison_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 80)
    print("최종 비교표")
    print("=" * 80)

    print(
        comparison_df.to_string(
            index=False
        )
    )

    print("\n비교표 저장:")
    print(comparison_path)


if __name__ == "__main__":
    main()