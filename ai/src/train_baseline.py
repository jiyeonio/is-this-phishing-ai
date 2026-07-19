from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)


# ============================================================
# 1. 기본 설정
# ============================================================

SEED = 42
MODEL_NAME = "beomi/KcELECTRA-base-v2022"

MAX_LENGTH = 256
TRAIN_BATCH_SIZE = 4
EVAL_BATCH_SIZE = 8
GRADIENT_ACCUMULATION_STEPS = 4

LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
NUM_EPOCHS = 2

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models" / "kcelectra_baseline"
RESULT_DIR = PROJECT_ROOT / "results" / "kcelectra_baseline"

TRAIN_PATH = PROCESSED_DIR / "train_real.csv"
VALIDATION_PATH = PROCESSED_DIR / "validation_real.csv"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. 재현성 설정
# ============================================================

def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ============================================================
# 3. 데이터 읽기
# ============================================================

def read_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: {path}\n"
            "먼저 python -m src.group_split 을 실행하세요."
        )

    df = pd.read_csv(path, encoding="utf-8-sig")

    required_columns = {
        "text",
        "label",
        "structured_family",
        "content",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"필수 컬럼이 없습니다: {sorted(missing_columns)}\n"
            f"현재 컬럼: {df.columns.tolist()}"
        )

    df = df.dropna(subset=["text", "label"]).copy()
    df["text"] = df["text"].astype(str)
    df["label"] = df["label"].astype(int)

    return df.reset_index(drop=True)


# ============================================================
# 4. 평가 지표
# ============================================================

def compute_metrics(eval_pred) -> dict[str, float]:
    logits, labels = eval_pred

    probabilities = torch.softmax(
        torch.tensor(logits),
        dim=1,
    ).numpy()

    phishing_probabilities = probabilities[:, 1]
    predictions = np.argmax(logits, axis=1)

    tn, fp, fn, tp = confusion_matrix(
        labels,
        predictions,
        labels=[0, 1],
    ).ravel()

    metrics = {
        "accuracy": accuracy_score(labels, predictions),
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
        "roc_auc": roc_auc_score(
            labels,
            phishing_probabilities,
        ),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }

    return metrics


# ============================================================
# 5. 한진 오탐 분석
# ============================================================

def save_validation_predictions(
    trainer: Trainer,
    validation_dataset: Dataset,
    validation_df: pd.DataFrame,
) -> None:
    prediction_output = trainer.predict(
        validation_dataset
    )

    logits = prediction_output.predictions

    probabilities = torch.softmax(
        torch.tensor(logits),
        dim=1,
    ).numpy()

    result_df = validation_df.copy()

    result_df["normal_probability"] = probabilities[:, 0]
    result_df["phishing_probability"] = probabilities[:, 1]
    result_df["prediction"] = np.argmax(
        probabilities,
        axis=1,
    )

    result_df["is_correct"] = (
        result_df["prediction"]
        == result_df["label"]
    )

    prediction_path = (
        RESULT_DIR
        / "validation_predictions.csv"
    )

    result_df.to_csv(
        prediction_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nValidation 예측 저장:")
    print(prediction_path)

    hanjin_df = result_df[
        result_df["structured_family"]
        .eq("hanjin_pickup")
    ].copy()

    print("\n" + "=" * 80)
    print("한진택배 validation 결과")
    print("=" * 80)

    print("한진 전체 수:", len(hanjin_df))

    if hanjin_df.empty:
        print(
            "한진택배 데이터가 없습니다. "
            "structured_family 값을 확인하세요."
        )
        return

    hanjin_fp = int(
        (
            (hanjin_df["label"] == 0)
            & (hanjin_df["prediction"] == 1)
        ).sum()
    )

    hanjin_correct = int(
        hanjin_df["is_correct"].sum()
    )

    print("정답 수:", hanjin_correct)
    print("피싱 오탐 수:", hanjin_fp)
    print(
        "한진 오탐률:",
        round(hanjin_fp / len(hanjin_df), 4),
    )

    print(
        "평균 피싱 확률:",
        round(
            float(
                hanjin_df[
                    "phishing_probability"
                ].mean()
            ),
            6,
        ),
    )

    hanjin_path = (
        RESULT_DIR
        / "hanjin_validation_predictions.csv"
    )

    hanjin_df.to_csv(
        hanjin_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("한진 결과 저장:")
    print(hanjin_path)


# ============================================================
# 6. 학습
# ============================================================

def run_baseline_training() -> None:
    set_seed()

    print("=" * 80)
    print("KcELECTRA baseline 학습 시작")
    print("=" * 80)

    print("모델:", MODEL_NAME)
    print("장치:", "cuda" if torch.cuda.is_available() else "cpu")
    print("PyTorch:", torch.__version__)

    train_df = read_dataset(TRAIN_PATH)
    validation_df = read_dataset(VALIDATION_PATH)

    print("\nTrain shape:", train_df.shape)
    print("Validation shape:", validation_df.shape)

    print("\nTrain label 분포")
    print(train_df["label"].value_counts())

    print("\nValidation label 분포")
    print(validation_df["label"].value_counts())

    print("\nValidation family 분포")
    print(
        validation_df["structured_family"]
        .value_counts()
        .head(10)
    )

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    model = (
        AutoModelForSequenceClassification
        .from_pretrained(
            MODEL_NAME,
            num_labels=2,
            id2label={
                0: "NORMAL",
                1: "PHISHING",
            },
            label2id={
                "NORMAL": 0,
                "PHISHING": 1,
            },
        )
    )

    train_dataset = Dataset.from_pandas(
        train_df[["text", "label"]],
        preserve_index=False,
    )

    validation_dataset = Dataset.from_pandas(
        validation_df[["text", "label"]],
        preserve_index=False,
    )

    def tokenize_batch(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=MAX_LENGTH,
        )

    train_dataset = train_dataset.map(
        tokenize_batch,
        batched=True,
        desc="Train tokenization",
    )

    validation_dataset = validation_dataset.map(
        tokenize_batch,
        batched=True,
        desc="Validation tokenization",
    )

    train_dataset = train_dataset.remove_columns(
        ["text"]
    )

    validation_dataset = (
        validation_dataset.remove_columns(
            ["text"]
        )
    )

    data_collator = DataCollatorWithPadding(
        tokenizer=tokenizer
    )

    training_args = TrainingArguments(
        output_dir=str(MODEL_DIR),

        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        num_train_epochs=NUM_EPOCHS,

        per_device_train_batch_size=(
            TRAIN_BATCH_SIZE
        ),
        per_device_eval_batch_size=(
            EVAL_BATCH_SIZE
        ),
        gradient_accumulation_steps=(
            GRADIENT_ACCUMULATION_STEPS
        ),

        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=100,

        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,

        save_total_limit=1,
        seed=SEED,
        data_seed=SEED,

        fp16=torch.cuda.is_available(),
        dataloader_num_workers=0,

        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    train_result = trainer.train()

    print("\n학습 완료")
    print(train_result)

    trainer.save_model(
        str(MODEL_DIR / "best_model")
    )

    tokenizer.save_pretrained(
        str(MODEL_DIR / "best_model")
    )

    validation_metrics = trainer.evaluate(
        validation_dataset
    )

    print("\nValidation 최종 성능")

    for key, value in validation_metrics.items():
        print(f"{key}: {value}")

    metrics_path = (
        RESULT_DIR
        / "validation_metrics.json"
    )

    with open(
        metrics_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            validation_metrics,
            file,
            ensure_ascii=False,
            indent=2,
        )

    save_validation_predictions(
        trainer=trainer,
        validation_dataset=validation_dataset,
        validation_df=validation_df,
    )

    print("\n" + "=" * 80)
    print("Baseline 학습 및 평가 완료")
    print("=" * 80)

    print("모델 저장:")
    print(MODEL_DIR / "best_model")

    print("결과 저장:")
    print(RESULT_DIR)


if __name__ == "__main__":
    run_baseline_training()