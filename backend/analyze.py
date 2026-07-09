"""분석 오케스트레이터 (계약 ①⑤ 관통).

문자 한 건을 받아 신호들을 모아 최종 응답(dict)을 조립한다:

    preprocess → classifier(model) · rules(rule) · reputation(rep) · graph(cluster)
              → fusion.fuse → (cluster면 소폭 가산) → fusion.level
              → explain → AnalyzeResponse 형태 dict

엔진(classifier·rules·reputation·graph)은 각 모듈 임포트 시 1회 초기화되어
프로세스 내내 재사용됨. 신고(/api/report)로 데이터가 바뀌면 graph.invalidate()
로 그래프만 갱신한다 (record_report 참고).
"""

from ai import fusion
from ai.classifier import predict_proba
from ai.preprocess import preprocess
from backend import graph, reputation, rules
from backend.explain import explain

# 클러스터에 걸릴 때 위험도 가산량 (소폭). 조직 위험도에 비례.
_CLUSTER_BONUS = 0.10


def analyze(text: str, sender: str | None = None) -> dict:
    """문자 -> AnalyzeResponse 형태 dict (계약 ①)."""
    pre = preprocess(text, sender)

    # 세 신호 (엔진 재사용)
    model_p = predict_proba(pre["masked"])
    rule_s, rule_ev = rules.analyze(pre)
    rep_s, rep_ev = reputation.lookup(pre)
    cluster = graph.match_cluster(pre)

    # 융합 → 위험도
    score = fusion.fuse(model_p, rule_s, rep_s)

    # 조직 클러스터에 걸리면 위험도 소폭 가산 (조직 위험도 비례)
    if cluster:
        score = round(min(1.0, score + _CLUSTER_BONUS * cluster["risk"]), 4)

    level = fusion.level(score)

    # evidence 는 rules + reputation 합침 (형식 {type,detail,weight} 통일)
    evidence = rule_ev + rep_ev

    # signals 순서 고정: model → rule → reputation (계약 ①)
    signals = {"model": model_p, "rule": rule_s, "reputation": rep_s}

    reasons = explain(evidence, level, score, cluster)

    return {
        "risk_score": score,
        "level": level,
        "reasons": reasons,
        "evidence": evidence,
        "signals": signals,
        "cluster": cluster,
    }


def record_report(text: str, sender: str | None = None) -> int:
    """신고 저장 + 그래프 갱신. 갱신 후 cluster_count 반환 (/api/report 용)."""
    reputation.add_report(text, sender)
    graph.invalidate()          # 데이터 바뀜 → 다음 접근 때 그래프 재계산
    return graph.to_json()["cluster_count"]
