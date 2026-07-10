// 방금 신고한 문자와 매칭되는 그래프 노드 id 집합을 계산.
// 백엔드 응답은 그대로 두고(계약 불변), 프론트에서 navigate state 로 받은
// 신고 문자(text/sender/urls)를 노드 id/label 과 대조해 강조 대상만 고른다.

// URL/도메인에서 호스트만 추출 (스킴·www·경로 제거) — backend domain_of 와 동일 규칙
function hostOf(url) {
  return String(url || '')
    .replace(/^https?:\/\//i, '')
    .replace(/^www\./i, '')
    .split('/')[0]
    .split('?')[0]
    .split(':')[0]
    .toLowerCase()
}

// 텍스트 본문에서 URL/도메인 후보를 뽑아 호스트로 변환
const URL_RE = /(?:https?:\/\/|www\.)[^\s<>"']+|(?<![@\w.])[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9-]{1,63})+(?:\/[^\s<>"']*)?/gi

function hostsFromText(text) {
  const out = []
  for (const m of String(text || '').matchAll(URL_RE)) {
    const h = hostOf(m[0].replace(/[.,);\]。]+$/, ''))
    if (h) out.push(h)
  }
  return out
}

// url 노드 label 은 등록도메인(eTLD+1)이라, 신고 호스트가 그 도메인이거나
// 서브도메인이면 매칭 (a1.yhanwh.site ⊇ yhanwh.site)
function hostMatchesLabel(host, label) {
  return host === label || host.endsWith('.' + label)
}

export function computeHighlightIds(graph, reported) {
  const ids = new Set()
  if (!graph?.nodes || !reported) return ids

  // navigate state 는 reportedText/reportedUrls/reportedSender 로 넘어옴.
  // (구 필드명 text/urls 도 fallback 으로 받아 호환)
  const text = reported.reportedText ?? reported.text ?? ''
  const hosts = [
    ...(reported.reportedUrls ?? reported.urls ?? []).map(hostOf),
    ...hostsFromText(text),
  ].filter(Boolean)

  // 강조는 신고한 URL(등록도메인) 노드로만 한정.
  // 흔한 문구/번호는 여러 조직에 흩어져 과잉 강조되므로 제외한다.
  for (const node of graph.nodes) {
    if (node.type === 'url' && hosts.some((h) => hostMatchesLabel(h, node.label))) {
      ids.add(node.id)
    }
  }
  return ids
}
