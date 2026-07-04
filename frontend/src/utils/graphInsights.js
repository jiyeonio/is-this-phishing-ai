// graph의 edges 연결 수(degree)를 "많이 언급/신고된 정도"의 근사치로 사용
export function getTopNumbers(graph, limit = 4) {
  if (!graph?.nodes) return []

  const degree = {}
  graph.edges?.forEach(({ source, target }) => {
    degree[source] = (degree[source] ?? 0) + 1
    degree[target] = (degree[target] ?? 0) + 1
  })

  return graph.nodes
    .filter((node) => node.type === 'number')
    .map((node) => ({ label: node.label, count: degree[node.id] ?? 0 }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
}
