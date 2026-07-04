import { useEffect, useState } from 'react'
import { Phone, Link2, Search, ShieldAlert, ShieldCheck } from 'lucide-react'
import { getGraph } from '../api/client'
import { MOCK_GRAPH } from '../utils/mockGraph'

const CARD_CLASS = 'rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-8'

const SEARCH_TYPES = [
  { key: 'number', label: '번호', icon: Phone, placeholder: '예: 010-1234-5678' },
  { key: 'url', label: 'URL', icon: Link2, placeholder: '예: bit.ly/abcxyz' },
]

// 정확 일치 대신, 번호는 숫자만 비교하고 URL은 대소문자 무시 부분일치로 비교
function normalize(type, value) {
  return type === 'number'
    ? value.replace(/[^0-9]/g, '')
    : value.trim().toLowerCase()
}

// 발신번호/URL이 그래프(피싱 조직 네트워크)에 존재하는지 조회 — getGraph()로 이미 받는 데이터 재사용, 새 백엔드 호출 없음
function findReport(graph, type, query) {
  const normalized = normalize(type, query)
  if (!normalized) return undefined

  const node = graph.nodes?.find(
    (n) =>
      n.type === type &&
      (type === 'number'
        ? n.label.replace(/[^0-9]/g, '') === normalized
        : n.label.toLowerCase().includes(normalized)),
  )
  if (!node) return null

  const connectedIds = new Set(
    graph.edges
      ?.filter((e) => e.source === node.id || e.target === node.id)
      .map((e) => (e.source === node.id ? e.target : e.source)),
  )
  const related = graph.nodes.filter((n) => connectedIds.has(n.id))

  return { node, related }
}

function Lookup() {
  const [graph, setGraph] = useState(null)
  const [type, setType] = useState('number')
  const [query, setQuery] = useState('')
  const [report, setReport] = useState(undefined)

  useEffect(() => {
    getGraph()
      .then(setGraph)
      .catch((err) => console.error('그래프 로드 실패:', err))
  }, [])

  const activeType = SEARCH_TYPES.find((t) => t.key === type)

  const handleSearch = () => {
    setReport(findReport(graph ?? MOCK_GRAPH, type, query))
  }

  const handleTypeChange = (key) => {
    setType(key)
    setQuery('')
    setReport(undefined)
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <Search className="text-blue-600" size={22} strokeWidth={2.25} />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            번호·URL 조회
          </h1>
        </div>
        <p className="text-sm text-slate-500">
          받은 전화·문자의 발신번호나 링크가 신고 이력이 있는지 바로
          확인하세요.
        </p>
      </div>

      <div className={CARD_CLASS}>
        <div className="flex flex-col gap-4">
          <div className="inline-flex w-fit gap-1 rounded-full bg-slate-100 p-1">
            {SEARCH_TYPES.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                type="button"
                onClick={() => handleTypeChange(key)}
                className={`flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-sm font-medium transition ${
                  type === key
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <Icon size={14} strokeWidth={2.25} />
                {label}
              </button>
            ))}
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder={activeType.placeholder}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 placeholder-slate-400 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/20"
            />
            <button
              type="button"
              onClick={handleSearch}
              className="flex flex-shrink-0 items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:from-blue-500 hover:to-cyan-500 active:scale-[0.98] active:from-blue-700 active:to-cyan-700"
            >
              <Search size={16} strokeWidth={2.25} />
              조회
            </button>
          </div>
        </div>
      </div>

      {report === null && (
        <div
          className={`flex items-start gap-3 ${CARD_CLASS} [animation:card-in_0.35s_ease-out]`}
        >
          <ShieldCheck size={18} className="mt-0.5 flex-shrink-0 text-emerald-500" />
          <div className="flex flex-col gap-1 text-sm">
            <p className="font-semibold text-slate-800">신고 이력이 없습니다</p>
            <p className="text-slate-500">
              PhishGuard DB에 등록된 신고 기록이 없습니다. 다만 신고 이력이
              없다고 100% 안전을 보장하지는 않으니 유의하세요.
            </p>
          </div>
        </div>
      )}

      {report && (
        <div
          className={`flex flex-col gap-4 ${CARD_CLASS} [animation:card-in_0.35s_ease-out]`}
        >
          <div className="flex items-start gap-3">
            <ShieldAlert size={18} className="mt-0.5 flex-shrink-0 text-red-500" />
            <div className="flex flex-col gap-1 text-sm">
              <p className="font-semibold text-red-700">
                {report.node.label} — 신고 이력이 있습니다
              </p>
              <p className="text-slate-500">
                함께 신고된 URL·문구입니다. 유사한 내용을 받았다면 스미싱을
                의심하세요.
              </p>
            </div>
          </div>

          {report.related.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {report.related.map((n) => (
                <span
                  key={n.id}
                  className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600"
                >
                  <span className="font-semibold text-slate-400">
                    {n.type}
                  </span>
                  {' · '}
                  {n.label}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Lookup
