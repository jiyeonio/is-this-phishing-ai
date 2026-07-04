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

function OrgGraph({ graph = MOCK_GRAPH }) {
  const data = {
    nodes: graph[GRAPH_FIELDS.nodes],
    links: graph[GRAPH_FIELDS.edges],
  }

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
          graphData={data}
          backgroundColor="#F8FAFC"
          nodeAutoColorBy="cluster"
          nodeColor={(node) => NODE_TYPE_COLORS[node.type] ?? DEFAULT_NODE_COLOR}
          nodeLabel={(node) => `${node.type}: ${node.label}`}
          linkColor={() => 'rgba(100, 116, 139, 0.35)'}
          nodeRelSize={5}
        />
      </div>
    </div>
  )
}

export default OrgGraph
