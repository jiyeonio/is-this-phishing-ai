import { useEffect, useMemo, useRef } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { Network } from 'lucide-react'
import { MOCK_GRAPH } from '../utils/mockGraph'

// API 응답 필드명이 바뀌면 이 값들만 고치면 됨
const GRAPH_FIELDS = {
  nodes: 'nodes',
  edges: 'edges',
  clusterCount: 'cluster_count',
}

const NODE_TYPE_COLORS = {
  number: '#0284c7',
  url: '#db2777',
  phrase: '#ca8a04',
}
const DEFAULT_NODE_COLOR = '#64748b'
// 방금 신고한 URL 노드 강조색 — 선명한 파랑(번호 노드의 연한 파랑과 톤 구분)
const HIGHLIGHT_COLOR = '#2563eb'

const LEGEND_ITEMS = [
  { type: 'number', label: '번호' },
  { type: 'url', label: 'URL' },
  { type: 'phrase', label: '문구' },
]

const EMPTY_SET = new Set()

// 강조 URL 노드를 통째로 다시 그림('replace'): 차분한 파랑 원 + 링 + 라벨.
// 네온/글로우/pulse 없음 — 은은하게 눈에만 띄게.
function drawHighlightNode(node, ctx, globalScale) {
  const r = 7.5 // 기본 노드(반지름 5)의 약 1.5배

  // 본체(선명한 파랑)
  ctx.beginPath()
  ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
  ctx.fillStyle = HIGHLIGHT_COLOR
  ctx.fill()

  // 얇은 링으로 살짝 강조
  ctx.lineWidth = 2 / globalScale
  ctx.strokeStyle = '#1e3a8a'
  ctx.beginPath()
  ctx.arc(node.x, node.y, r + 2, 0, 2 * Math.PI)
  ctx.stroke()

  // 라벨(무엇이 신고됐는지 바로 보이게)
  const fontSize = Math.max(11 / globalScale, r * 0.9)
  ctx.font = `600 ${fontSize}px sans-serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  ctx.fillStyle = '#1e3a8a'
  ctx.fillText(node.label ?? '', node.x, node.y + r + 3)
}

function OrgGraph({ graph = MOCK_GRAPH, highlightIds = EMPTY_SET }) {
  const fgRef = useRef(null)
  const nodes = graph[GRAPH_FIELDS.nodes]
  const edges = graph[GRAPH_FIELDS.edges]

  // graphData 를 안정화(불필요한 시뮬레이션 재가열/좌표 리셋 방지)
  const data = useMemo(() => ({ nodes, links: edges }), [nodes, edges])
  const hasHighlight = highlightIds.size > 0

  // 강조 노드로 화면을 자동 이동/줌 (좌표가 잡힐 시간을 두고)
  useEffect(() => {
    if (!hasHighlight) return
    const timer = setTimeout(() => {
      const fg = fgRef.current
      if (!fg) return
      const targets = (data.nodes ?? []).filter(
        (n) => highlightIds.has(n.id) && n.x != null && n.y != null,
      )
      if (!targets.length) return
      const cx = targets.reduce((s, n) => s + n.x, 0) / targets.length
      const cy = targets.reduce((s, n) => s + n.y, 0) / targets.length
      fg.centerAt(cx, cy, 800)
      fg.zoom(3.2, 800)
    }, 800)
    return () => clearTimeout(timer)
  }, [highlightIds, hasHighlight, data])

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-8 [animation:card-in_0.35s_ease-out]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Network size={16} className="text-slate-400" strokeWidth={2.25} />
          <p className="text-sm font-medium text-slate-700">
            피싱 조직 네트워크
          </p>
        </div>
        <span className="text-xs text-slate-400">
          클러스터 {graph[GRAPH_FIELDS.clusterCount]}개
        </span>
      </div>

      <div className="h-[420px] w-full overflow-hidden rounded-xl border border-slate-200">
        <ForceGraph2D
          ref={fgRef}
          graphData={data}
          backgroundColor="#F8FAFC"
          nodeAutoColorBy="cluster"
          nodeColor={(node) => NODE_TYPE_COLORS[node.type] ?? DEFAULT_NODE_COLOR}
          nodeLabel={(node) => `${node.type}: ${node.label}`}
          linkColor={() => 'rgba(100, 116, 139, 0.35)'}
          nodeRelSize={5}
          nodeVal={(node) => (highlightIds.has(node.id) ? 2.5 : 1)}
          nodeCanvasObjectMode={(node) =>
            highlightIds.has(node.id) ? 'replace' : undefined
          }
          nodeCanvasObject={(node, ctx, globalScale) => {
            if (highlightIds.has(node.id)) drawHighlightNode(node, ctx, globalScale)
          }}
        />
      </div>

      <div className="flex flex-wrap gap-3">
        {LEGEND_ITEMS.map(({ type, label }) => (
          <span
            key={type}
            className="flex items-center gap-1.5 text-xs text-slate-500"
          >
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: NODE_TYPE_COLORS[type] }}
            />
            {label}
          </span>
        ))}
        {hasHighlight && (
          <span
            className="flex items-center gap-1.5 text-xs font-semibold"
            style={{ color: HIGHLIGHT_COLOR }}
          >
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: HIGHLIGHT_COLOR }}
            />
            방금 신고한 URL
          </span>
        )}
      </div>
    </div>
  )
}

export default OrgGraph
