"""신호 융합 (계약 ⑤).

    fusion.fuse(model_p, rule_s, rep_s: float) -> float
    fusion.level(score: float) -> str

융합 원칙:
- 문자모델 확률 model_p를 기본 위험도로 사용한다.
- URL 규칙 rule_s와 신고 평판 rep_s는 위험도를 낮추지 않는다.
- 추가 위험 신호가 존재할 때 남은 안전 확률을 단계적으로 줄인다.
- fuse/level 시그니처와 반환 범위는 기존 계약을 유지한다.
"""

import config


def _clamp(value: float) -> float:
    """입력값을 0~1 범위로 제한한다."""
    return min(max(float(value), 0.0), 1.0)


def fuse(
    model_p: float,
    rule_s: float,
    rep_s: float,
) -> float:
    """문자모델 확률을 보존하면서 규칙·평판 신호로 위험도를 상향한다."""

    model_p = _clamp(model_p)
    rule_s = _clamp(rule_s)
    rep_s = _clamp(rep_s)

    # 문자모델을 기본 위험도로 사용
    score = model_p

    # URL 규칙 신호가 있으면 남아 있는 안전 확률 일부를 위험도로 전환
    score += (1.0 - score) * rule_s

    # 신고 이력이 있으면 다시 남은 안전 확률 일부를 위험도로 전환
    score += (1.0 - score) * rep_s

    return round(_clamp(score), 4)


def level(score: float) -> str:
    """0~1 위험도 -> 'safe' | 'suspicious' | 'danger'."""
    score = _clamp(score)

    if score >= config.THRESHOLD_DANGER:
        return "danger"

    if score >= config.THRESHOLD_SUSPICIOUS:
        return "suspicious"

    return "safe"