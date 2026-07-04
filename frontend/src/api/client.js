// C 트랙 API 클라이언트 — 개발가이드 계약 ①②③ + B6(신고/트렌드) 기준.
// 백엔드가 INTEGRATION.md 계약대로 응답하면 이 파일은 손댈 필요 없음.
// 계약 필드명이 바뀌면 normalize.js만 고치면 됨(analyze/report는 계약이 고정이라 정규화 없이 그대로 전달).
import { normalizeGraph, normalizeTrends } from './normalize'

async function handleResponse(res) {
  if (!res.ok) {
    throw new Error(`요청 실패 (${res.status})`);
  }
  return res.json();
}

// 계약 ①: POST /api/analyze { text, sender } → AnalyzeResponse
// (risk_score, level, reasons, evidence, signals, cluster, + 예정: urls)
export const analyze = (text, sender) =>
  fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, sender }),
  }).then(handleResponse);

// 계약 ②: GET /api/graph → { nodes, edges, cluster_count }
export const getGraph = () =>
  fetch("/api/graph").then(handleResponse).then(normalizeGraph);

// B6 신규, 계약 미확정: GET /api/trends → { top_phrases, top_urls, top_orgs }
export const getTrends = () =>
  fetch("/api/trends").then(handleResponse).then(normalizeTrends);

// 계약 ③: POST /api/report { text, sender } — 응답 바디는 사용하지 않음(성공 여부만 확인)
export const report = (text, sender) =>
  fetch("/api/report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, sender }),
  }).then(handleResponse);
