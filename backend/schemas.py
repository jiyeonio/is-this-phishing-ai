"""요청/응답 스키마 (계약 ①②③).

필드명·범위·null 규칙이 프론트(C)와의 계약. 여기 어긋나면 전체가 안 붙음.
- 필드명은 snake_case 고정 (risk_score O, riskScore X)
- 위험도(risk_score, weight, risk, signals 값)는 전부 0~1 실수 (0~100 아님)
- level 은 "safe" | "suspicious" | "danger" 셋 중 하나
- cluster 는 null 가능 (조직 매칭 안 되면 없음)
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

# level 값 3종 고정 (계약 ①)
Level = Literal["safe", "suspicious", "danger"]


# --- ① /api/analyze ----------------------------------------------------
class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="문자 본문")
    sender: Optional[str] = Field(None, description="발신번호 (선택, null 가능)")


class Evidence(BaseModel):
    """탐지 근거 1건. rules/reputation 이 내놓는 형식과 동일 (계약 ⑤).

    이 형식이 그대로 /api/analyze 의 evidence 로 나가고 explain 입력이 됨.
    """

    type: str = Field(..., description="근거 종류 (예: '단축 URL')")
    detail: str = Field(..., description="구체 값 (예: 'bit.ly')")
    weight: float = Field(..., description="기여 가중치 0~1")


class Signals(BaseModel):
    """신호별 원점수 (투명성용, 프론트 3-바 표시)."""

    model: float = Field(..., description="문자모델 점수 0~1")
    rule: float = Field(..., description="규칙 점수 0~1")
    reputation: float = Field(..., description="평판 점수 0~1")


class Cluster(BaseModel):
    """매칭된 조직 클러스터 요약 (null 가능)."""

    id: str = Field(..., description="클러스터 id (예: '조직-0')")
    size: int = Field(..., description="클러스터 노드 수")
    report_count: int = Field(..., description="누적 신고 수")
    risk: float = Field(..., description="클러스터 위험도 0~1")


class AnalyzeResponse(BaseModel):
    risk_score: float = Field(..., description="최종 위험도 0~1 (0~100 아님)")
    level: Level = Field(..., description="safe | suspicious | danger")
    reasons: list[str] = Field(
        default_factory=list, description="사람이 읽는 근거 문장 배열"
    )
    evidence: list[Evidence] = Field(
        default_factory=list, description="구조화 근거 목록"
    )
    signals: Signals = Field(..., description="신호별 원점수")
    cluster: Optional[Cluster] = Field(
        None, description="조직 클러스터 (매칭 없으면 null)"
    )


# --- ② /api/graph ------------------------------------------------------
class GraphNode(BaseModel):
    id: str = Field(..., description="노드 id (예: 'url:xnr.ae1t.yachts')")
    label: str = Field(..., description="화면 표시 라벨")
    type: Literal["number", "url", "phrase"] = Field(
        ..., description="노드 종류 (색 구분)"
    )
    cluster: int = Field(..., description="클러스터 정수 id (그룹/색 묶음)")


class GraphEdge(BaseModel):
    # 주의: 프론트 라이브러리(react-force-graph)는 links 를 기대 →
    # 프론트가 edges→links 로 이름만 매핑 (계약 ②).
    source: str = Field(..., description="시작 노드 id")
    target: str = Field(..., description="끝 노드 id")


class GraphResponse(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    cluster_count: int = Field(0, description="클러스터 개수")


# --- ③ /api/report -----------------------------------------------------
class ReportRequest(BaseModel):
    text: str = Field(..., description="신고할 문자 본문")
    sender: Optional[str] = Field(None, description="발신번호 (선택)")


class ReportResponse(BaseModel):
    ok: bool = Field(True, description="신고 접수 여부")
    cluster_count: int = Field(..., description="갱신 후 클러스터 개수")


# --- 헬스체크 ----------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = Field("ok")
