"""KcELECTRA 문자 피싱 분류기.

계약:
    classifier.predict_proba(masked_text: str) -> float

반환값:
    0.0~1.0 범위의 피싱 확률
"""

from pathlib import Path

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


# classifier.py가 ai 폴더 안에 있으므로
# ai/models/text_clf 경로를 가리킨다.
AI_DIR = Path(__file__).resolve().parent
MODEL_DIR = AI_DIR / "models" / "text_clf"

MAX_LENGTH = 256


if not MODEL_DIR.exists():
    raise FileNotFoundError(
        f"KcELECTRA 모델 폴더를 찾을 수 없습니다: {MODEL_DIR}"
    )


# CPU 또는 GPU 자동 선택
DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


print(f"[classifier] 모델 로딩 시작: {MODEL_DIR}")


tokenizer = AutoTokenizer.from_pretrained(
    MODEL_DIR,
    local_files_only=True,
)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_DIR,
    local_files_only=True,
)

model.to(DEVICE)
model.eval()


print(
    f"[classifier] KcELECTRA 로드 완료 "
    f"(device={DEVICE})"
)


def predict_proba(masked_text: str) -> float:
    """전처리된 문자에서 피싱 확률을 반환한다."""

    if masked_text is None:
        return 0.0

    text = str(masked_text).strip()

    if not text:
        return 0.0

    encoded = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_LENGTH,
        padding=True,
    )

    encoded = {
        key: value.to(DEVICE)
        for key, value in encoded.items()
    }

    with torch.inference_mode():
        logits = model(**encoded).logits

        probabilities = torch.softmax(
            logits,
            dim=-1,
        )

        # 학습 라벨:
        # 0 = 정상
        # 1 = 피싱
        phishing_probability = probabilities[0, 1].item()

    return round(float(phishing_probability), 4)