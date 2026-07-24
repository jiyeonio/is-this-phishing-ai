"""문자모델 분류기 (계약 ⑤).

classifier.predict_proba(masked_text: str) -> float

- 입력: URL이 마스킹된 텍스트
- 출력: 피싱 클래스 확률(0~1)
- 모델: ai/models/text_clf/
"""

from __future__ import annotations

from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


_MODEL_DIR = Path(__file__).resolve().parent / "models" / "text_clf"

_tokenizer = None
_model = None
_device = None


def _load_model() -> None:
    """저장된 텍스트 분류모델을 최초 1회만 로드한다."""
    global _tokenizer, _model, _device

    if _tokenizer is not None and _model is not None:
        return

    if not _MODEL_DIR.exists():
        raise FileNotFoundError(
            f"텍스트 모델 폴더를 찾을 수 없습니다: {_MODEL_DIR}"
        )

    required_files = [
        _MODEL_DIR / "config.json",
        _MODEL_DIR / "model.safetensors",
        _MODEL_DIR / "tokenizer.json",
        _MODEL_DIR / "tokenizer_config.json",
    ]

    missing_files = [
        str(path)
        for path in required_files
        if not path.exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            "텍스트 모델 필수 파일이 없습니다:\n"
            + "\n".join(missing_files)
        )

    _device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    _tokenizer = AutoTokenizer.from_pretrained(
        _MODEL_DIR,
        local_files_only=True,
    )

    _model = AutoModelForSequenceClassification.from_pretrained(
        _MODEL_DIR,
        local_files_only=True,
    )

    _model.to(_device)
    _model.eval()


def _phishing_label_id() -> int:
    """
    모델 config에서 피싱 클래스 ID를 확인한다.

    일반적으로:
    - 0 = NORMAL
    - 1 = PHISHING
    """
    _load_model()

    config = _model.config

    label2id = getattr(config, "label2id", None) or {}

    normalized = {
        str(label).upper(): int(label_id)
        for label, label_id in label2id.items()
    }

    for candidate in (
        "PHISHING",
        "SMISHING",
        "LABEL_1",
        "1",
    ):
        if candidate in normalized:
            return normalized[candidate]

    # 현재 프로젝트의 학습 라벨 계약:
    # 0 = 정상, 1 = 피싱
    if getattr(config, "num_labels", 2) == 2:
        return 1

    raise ValueError(
        f"피싱 라벨 ID를 확인할 수 없습니다. label2id={label2id}"
    )


def predict_proba(masked_text: str) -> float:
    """마스킹 텍스트에서 피싱 확률을 반환한다."""
    if masked_text is None:
        masked_text = ""

    text = str(masked_text).strip()

    if not text:
        return 0.0

    _load_model()

    encoded = _tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding=False,
    )

    encoded = {
        key: value.to(_device)
        for key, value in encoded.items()
    }

    with torch.no_grad():
        outputs = _model(**encoded)
        probabilities = torch.softmax(
            outputs.logits,
            dim=-1,
        )

    phishing_id = _phishing_label_id()

    probability = probabilities[0, phishing_id].item()

    return float(probability)