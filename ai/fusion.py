"""신호 융합 (계약 ⑤).

    fusion.fuse(model_p, rule_s, rep_s: float) -> float   # 세 신호 -> 최종 위험도 0~1
    fusion.level(score: float) -> str                     # 0~1 -> safe/suspicious/danger

⚠️ 최소 폴백 = 가중합. 실제로는 A가 메타분류기(models/fusion.pkl)를 학습해
이 파일을 교체함. 시그니처(fuse/level)와 반환 범위는 계약이라 유지.
level 임계값은 루트 config 에서 가져옴(전원 공유).
"""

import config

# 가중치 합 = 1.0. 규칙 신호를 조금 더 신뢰(명단 히트는 확실한 편).
_W_MODEL = 0.45
_W_RULE = 0.35
_W_REP = 0.20


def fuse(model_p: float, rule_s: float, rep_s: float) -> float:
    """세 신호의 가중합 -> 0~1 최종 위험도."""
    score = _W_MODEL * model_p + _W_RULE * rule_s + _W_REP * rep_s
    # 입력이 범위를 벗어나도 0~1 로 클램프
    return round(min(max(score, 0.0), 1.0), 4)


def level(score: float) -> str:
    """0~1 위험도 -> 'safe' | 'suspicious' | 'danger' (계약 ①)."""
    if score >= config.THRESHOLD_DANGER:
        return "danger"
    if score >= config.THRESHOLD_SUSPICIOUS:
        return "suspicious"
    return "safe"
