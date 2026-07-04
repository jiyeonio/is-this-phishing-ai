// 백엔드 응답을 프론트 전역에서 쓰는 표준 모양으로 맞추는 자리.
// INTEGRATION.md 계약이 확정/변경되면 이 파일만 고치면 되고,
// Analyze/Report/Trends/Lookup/OrgGraph 등 나머지 코드는 건드릴 필요 없음.

// 계약 ②: graph.to_json() → { nodes, edges, cluster_count }
// react-force-graph는 edges가 아니라 links를 기대하므로(가이드 C5 주석 참고),
// 혹시 백엔드가 links로 내려줘도 흡수하도록 폴백을 둠
export function normalizeGraph(raw) {
  if (!raw) return raw
  return {
    nodes: raw.nodes ?? [],
    edges: raw.edges ?? raw.links ?? [],
    cluster_count: raw.cluster_count ?? raw.clusterCount ?? 0,
  }
}

// 계약 미확정 구간: /api/trends (B6, "평판DB에서 최다 신고 도메인·문구 집계 반환")
// 정확한 필드명이 아직 안 나와서, 후보 키를 넓게 받아 label/count로 통일해둠.
// 실제 계약이 정해지면 아래 CANDIDATE_*_KEYS만 좁혀서 고치면 됨.
const CANDIDATE_LABEL_KEYS = ['label', 'phrase', 'url', 'domain', 'org', 'name', 'text']
const CANDIDATE_COUNT_KEYS = ['count', 'report_count', 'reports']

function pickField(item, candidates) {
  for (const key of candidates) {
    if (item[key] != null) return item[key]
  }
  return undefined
}

function normalizeTrendItems(items) {
  return (items ?? []).map((item) => ({
    label: String(pickField(item, CANDIDATE_LABEL_KEYS) ?? ''),
    count: Number(pickField(item, CANDIDATE_COUNT_KEYS) ?? 0),
  }))
}

export function normalizeTrends(raw) {
  if (!raw) return raw
  return {
    top_phrases: normalizeTrendItems(raw.top_phrases),
    top_urls: normalizeTrendItems(raw.top_urls),
    top_orgs: normalizeTrendItems(raw.top_orgs),
  }
}
