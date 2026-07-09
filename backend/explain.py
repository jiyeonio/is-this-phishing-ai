"""근거 설명 생성 (계약 ⑤ evidence -> 사람이 읽는 reasons).

    explain(evidence, level, score, cluster=None) -> list[str]

- ANTHROPIC_API_KEY 있으면 Claude(claude-haiku-4-5, temperature=0.0) 로 생성
- 키 없거나 호출 실패하면 템플릿 폴백 (키 빼도 데모 안전)
- 어느 경로든 reasons 는 list[str] 로 반환

⚠️ Claude 프롬프트에 "주어진 evidence 로만 설명, 없는 내용 추측 금지" 를 못박음.
temperature=0.0 (재현성·환각 최소화).
"""

import json

import config

_MODEL = "claude-haiku-4-5"

_SYSTEM_PROMPT = (
    "너는 스미싱(문자 피싱) 분석 결과를 사용자에게 설명하는 도우미다. "
    "반드시 아래 규칙을 지켜라:\n"
    "1) 주어진 evidence(증거) 목록에 있는 내용만 근거로 설명한다.\n"
    "2) evidence 에 없는 사실·수치·기관명·URL 은 절대 추측하거나 지어내지 않는다.\n"
    "3) 한국어로, 각 근거를 한 문장으로 간결하게 쓴다.\n"
    "4) 출력은 한 줄에 근거 하나씩. 번호·불릿 기호 없이 문장만 쓴다.\n"
    "5) 과장 없이 사실만. 증거가 약하면 약하다고 표현한다."
)


def _template_reasons(
    evidence: list[dict], level: str, score: float, cluster: dict | None
) -> list[str]:
    """Claude 없이도 동작하는 규칙 기반 근거 문장."""
    reasons: list[str] = []

    # 1) 상단 요약 (level 기준)
    pct = round(score * 100)
    if level == "danger":
        reasons.append(f"위험도 {pct}%로 스미싱(문자 피싱) 가능성이 높습니다.")
    elif level == "suspicious":
        reasons.append(f"위험도 {pct}%로 주의가 필요한 문자입니다.")
    else:
        reasons.append(f"위험도 {pct}%로 뚜렷한 피싱 신호는 없습니다.")

    # 2) evidence 타입별 문장 (행동 유도 문구는 하나로 묶음)
    action_words: list[str] = []
    for e in evidence:
        etype, detail = e.get("type", ""), e.get("detail", "")
        if etype == "피싱 URL 명단":
            reasons.append(f"신고된 피싱 URL 명단에 등록된 주소입니다 ({detail}).")
        elif etype == "단축 URL":
            reasons.append(f"실제 주소를 감추는 단축 URL이 포함되어 있습니다 ({detail}).")
        elif etype == "의심 TLD":
            reasons.append(f"피싱에 자주 쓰이는 도메인 형태입니다 ({detail}).")
        elif etype == "신고 이력 도메인":
            reasons.append(f"과거 신고 이력이 있는 도메인입니다 ({detail}).")
        elif etype == "유사 신고 문구":
            reasons.append(f"기존 신고 사례와 문구가 유사합니다 ({detail}).")
        elif etype == "행동 유도 문구":
            action_words.append(detail)
        elif detail:
            reasons.append(f"{etype}: {detail}")
    if action_words:
        joined = ", ".join(f"'{w}'" for w in action_words)
        reasons.append(f"{joined} 등 행동을 유도하는 문구가 포함되어 있습니다.")

    # 3) 클러스터 (조직 연결)
    if cluster:
        reasons.append(
            f"동일 조직으로 추정되는 클러스터({cluster.get('id')})에 연결되며, "
            f"관련 신고가 {cluster.get('report_count')}건 있습니다."
        )

    return reasons


def _claude_reasons(
    evidence: list[dict], level: str, score: float, cluster: dict | None
) -> list[str]:
    """Claude 로 근거 생성. 실패 시 예외를 올려 호출부에서 폴백."""
    import anthropic  # 지연 임포트 (키 없으면 아예 안 씀)

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    payload = {
        "risk_score": score,
        "level": level,
        "evidence": evidence,
        "cluster": cluster,
    }
    user_msg = (
        "다음은 한 문자에 대한 스미싱 분석 결과다. evidence 에 있는 내용만 근거로, "
        "사용자에게 왜 이 위험도가 나왔는지 한국어 근거 문장들을 만들어라. "
        "evidence 에 없는 내용은 절대 추측하지 마라.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )

    resp = client.messages.create(
        model=_MODEL,
        max_tokens=512,
        temperature=0.0,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = "".join(
        block.text for block in resp.content if getattr(block, "type", "") == "text"
    )
    reasons = [line.strip(" -•\t") for line in text.splitlines() if line.strip()]
    if not reasons:
        raise ValueError("Claude 응답이 비어 있음")
    return reasons


def explain(
    evidence: list[dict],
    level: str,
    score: float,
    cluster: dict | None = None,
) -> list[str]:
    """근거 문장 리스트 생성. 키 있으면 Claude, 없거나 실패하면 템플릿 폴백."""
    if config.ANTHROPIC_API_KEY:
        try:
            return _claude_reasons(evidence, level, score, cluster)
        except Exception:
            # 데모 안전: 어떤 이유로든 실패하면 조용히 템플릿으로
            pass
    return _template_reasons(evidence, level, score, cluster)
