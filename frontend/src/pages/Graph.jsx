import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Network, RotateCw, CheckCircle2, Phone } from 'lucide-react'
import { getGraph } from '../api/client'
import { MOCK_GRAPH } from '../utils/mockGraph'
import { getTopNumbers } from '../utils/graphInsights'
import OrgGraph from '../components/OrgGraph'
import RankedBarList from '../components/RankedBarList'

function Graph() {
  const location = useLocation()
  const [graph, setGraph] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  // 최초 로드는 새로고침 스피너 없이 조용히
  useEffect(() => {
    getGraph()
      .then(setGraph)
      .catch((err) => console.error('그래프 로드 실패:', err))
  }, [])

  // n27(그래프 갱신 요청) → n25(ForceGraph2D 렌더링): 사용자가 직접 누르는 새로고침
  const handleRefresh = () => {
    setRefreshing(true)
    getGraph()
      .then(setGraph)
      .catch((err) => console.error('그래프 로드 실패:', err))
      .finally(() => setRefreshing(false))
  }

  const activeGraph = graph ?? MOCK_GRAPH
  const topNumbers = getTopNumbers(activeGraph)

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <Network className="text-slate-900" size={22} strokeWidth={2.25} />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            조직 그래프
          </h1>
        </div>
        <p className="text-sm text-slate-500">
          신고된 번호·URL·문구가 어떻게 서로 연결돼 조직화됐는지 시각화합니다.
        </p>
      </div>

      {location.state?.justReported && (
        <p className="flex items-center gap-1.5 rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-900 [animation:card-in_0.3s_ease-out]">
          <CheckCircle2 size={15} strokeWidth={2.25} />
          신고 완료, 평판DB 반영됨 — 최신 그래프예요
        </p>
      )}

      <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm font-semibold text-slate-700">스미싱 조직 그래프</p>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:opacity-60"
        >
          <RotateCw
            size={13}
            strokeWidth={2.25}
            className={refreshing ? 'animate-spin' : ''}
          />
          {refreshing ? '새로고침 중...' : '그래프 갱신'}
        </button>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-center shadow-sm">
          <p className="text-xl font-bold text-slate-900">
            {activeGraph.nodes?.length ?? 0}
          </p>
          <p className="text-xs text-slate-400">연결 노드</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-center shadow-sm">
          <p className="text-xl font-bold text-slate-900">
            {activeGraph.edges?.length ?? 0}
          </p>
          <p className="text-xs text-slate-400">엣지 수</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-center shadow-sm">
          <p className="text-xl font-bold text-slate-900">
            {activeGraph.cluster_count ?? 0}
          </p>
          <p className="text-xs text-slate-400">클러스터</p>
        </div>
      </div>

      <OrgGraph graph={activeGraph} />

      {topNumbers.length > 0 && (
        <RankedBarList
          title="최근 많이 신고된 발신번호"
          icon={Phone}
          colorClass="bg-slate-900"
          items={topNumbers}
        />
      )}
    </div>
  )
}

export default Graph
