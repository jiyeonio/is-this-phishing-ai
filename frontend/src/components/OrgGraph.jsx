import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
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
  const wrapRef = useRef(null)
  const fittedRef = useRef(false)
  const [dims, setDims] = useState({ width: 0, height: 0 })
  const nodes = graph[GRAPH_FIELDS.nodes]
  const edges = graph[GRAPH_FIELDS.edges]

  // graphData 를 안정화(불필요한 시뮬레이션 재가열/좌표 리셋 방지)
  const data = useMemo(() => ({ nodes, links: edges }), [nodes, edges])
  const hasHighlight = highlightIds.size > 0

  // 컨테이너 실제 크기를 캔버스에 명시 전달 → 캔버스가 화면 박스와 정확히 일치.
  // (크기를 안 주면 캔버스가 컨테이너보다 커져, 원점 근처 노드들이 화면 구석에
  //  작게 몰려 보이고 zoomToFit/centerAt 이 엉뚱한 기준으로 계산되는 원인이 됨.)
  useLayoutEffect(() => {
    const el = wrapRef.current
    if (!el) return undefined
    const measure = () =>
      setDims({ width: el.clientWidth, height: el.clientHeight })
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // 강조 노드(들)의 중심으로 화면 이동 + 줌. 좌표가 잡힌 뒤에만 성공(true 반환).
  const focusHighlight = () => {
    const fg = fgRef.current
    if (!fg) return false
    const targets = (data.nodes ?? []).filter(
      (n) => highlightIds.has(n.id) && n.x != null && n.y != null,
    )
    if (!targets.length) return false
    const cx = targets.reduce((s, n) => s + n.x, 0) / targets.length
    const cy = targets.reduce((s, n) => s + n.y, 0) / targets.length
    fg.centerAt(cx, cy, 800)
    fg.zoom(3.2, 800)
    return true
  }

  // 전체 그래프를 화면에 꽉 차게 프레이밍(강조가 없을 때).
  const fitAll = () => fgRef.current?.zoomToFit(400, 50)

  // 데이터가 바뀌면(첫 로드/갱신) 프레이밍을 다시 하고, 힘을 재설정해 재가열.
  // 노드가 성게처럼 뭉치지 않게 반발력·링크 거리를 키운다.
  useEffect(() => {
    fittedRef.current = false
    const fg = fgRef.current
    if (!fg) return
    fg.d3Force('charge')?.strength(-140).distanceMax(320)
    fg.d3Force('link')?.distance(34)
    fg.d3ReheatSimulation()
  }, [data])

  // 강조가 켜졌는데 엔진이 이미 멈춰 onEngineStop 이 안 오는 경우의 폴백.
  // 좌표가 잡힐 때까지 짧게 몇 번 재시도한 뒤 성공하면 멈춘다.
  useEffect(() => {
    if (!hasHighlight) return undefined
    let tries = 0
    const timer = setInterval(() => {
      tries += 1
      if (focusHighlight() || tries >= 10) clearInterval(timer)
    }, 200)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightIds, hasHighlight, data])

  // 크기가 바뀌면(반응형/리사이즈) 강조가 없을 때 다시 화면에 맞춘다.
  useEffect(() => {
    if (dims.width && fittedRef.current && !hasHighlight) fitAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dims.width, dims.height])

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

      <div
        ref={wrapRef}
        className="h-[420px] w-full overflow-hidden rounded-xl border border-slate-200"
      >
        <ForceGraph2D
          ref={fgRef}
          graphData={data}
          width={dims.width || undefined}
          height={dims.height || undefined}
          backgroundColor="#F8FAFC"
          nodeAutoColorBy="cluster"
          nodeColor={(node) => NODE_TYPE_COLORS[node.type] ?? DEFAULT_NODE_COLOR}
          nodeLabel={(node) => `${node.type}: ${node.label}`}
          linkColor={() => 'rgba(100, 116, 139, 0.35)'}
          nodeRelSize={6}
          // 대규모(~수백 노드) 렌더 안정화: 워밍업 후 정해진 틱만 돌고 멈춰
          // 시뮬레이션이 무한정 도는 것을 막고(성능), 멈추면 화면에 맞춰 프레이밍.
          warmupTicks={40}
          cooldownTicks={200}
          onEngineStop={() => {
            // 좌표가 확정된 시점. 강조가 있으면 그 노드로 센터링, 없으면 전체 맞춤.
            if (hasHighlight) {
              focusHighlight()
            } else if (!fittedRef.current) {
              fittedRef.current = true
              fitAll()
            }
          }}
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
