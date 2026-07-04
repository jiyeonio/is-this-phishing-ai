import { useState, useEffect } from 'react'
import { ShieldAlert, ScanSearch, Phone } from 'lucide-react'
import { analyze, getGraph } from '../api/client'
import Result from '../components/Result'
import OrgGraph from '../components/OrgGraph'
import RankedBarList from '../components/RankedBarList'
import { getTopNumbers } from '../utils/graphInsights'
import { MOCK_GRAPH } from '../utils/mockGraph'

// ============================================================
// 🚧 TEMP TEST MOCK — 백엔드 연결되면 이 블록과 아래 버튼 삭제할 것 🚧
// ============================================================
const MOCK_RESULT = {
  risk_score: 0.75,
  level: 'danger',
  reasons: ['의심스러운 단축 URL', '긴급성 유발 문구'],
  evidence: [
    { type: 'url', detail: 'bit.ly/3xAbCd' },
    { type: 'phrase', detail: '계좌가 정지됩니다' },
  ],
  signals: { model: 0.8, rule: 0.7, reputation: 0.65 },
  cluster: { org_count: 3, report_count: 12 },
}
// ============================================================

function Analyze() {
  const [text, setText] = useState('')
  const [sender, setSender] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [graph, setGraph] = useState(null)

  useEffect(() => {
    getGraph()
      .then(setGraph)
      .catch((err) => console.error('그래프 로드 실패:', err))
  }, [])

  const handleAnalyze = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await analyze(text, sender)
      setResult(data)
    } catch {
      setError('분석 요청에 실패했습니다. 잠시 후 다시 시도해주세요.')
    } finally {
      setLoading(false)
    }
  }

  // 🚧 TEMP TEST HANDLER — 위 MOCK_RESULT와 함께 삭제할 것 🚧
  const handleShowMockResult = () => {
    setError(null)
    setResult(MOCK_RESULT)
  }

  const topNumbers = getTopNumbers(graph ?? MOCK_GRAPH)

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <ShieldAlert className="text-blue-600" size={22} strokeWidth={2.25} />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            문자 위험도 분석
          </h1>
        </div>
        <p className="text-sm text-slate-500">
          수신한 문자를 그대로 붙여넣으면 AI가 스미싱 위험도를 즉시 분석합니다.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-8">
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-slate-700">
              문자 내용
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="문자 내용을 입력하세요"
              rows={6}
              className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 placeholder-slate-400 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-slate-700">
              발신번호 (선택)
            </label>
            <input
              type="text"
              value={sender}
              onChange={(e) => setSender(e.target.value)}
              placeholder="발신번호 (선택)"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 placeholder-slate-400 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={loading}
            className="mt-2 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:from-blue-500 hover:to-cyan-500 hover:shadow-blue-600/30 active:scale-[0.98] active:from-blue-700 active:to-cyan-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100"
          >
            <ScanSearch size={18} strokeWidth={2.25} />
            {loading ? '분석 중...' : '위험도 분석하기'}
          </button>

          {/* 🚧 TEMP TEST BUTTON — 백엔드 연결되면 삭제할 것 🚧 */}
          <button
            type="button"
            onClick={handleShowMockResult}
            className="rounded-xl border border-dashed border-amber-300 bg-amber-50 px-6 py-2.5 text-xs font-semibold text-amber-700 transition hover:bg-amber-100"
          >
            🚧 [테스트용] 목업 결과 보기
          </button>
        </div>
      </div>

      <Result
        result={result}
        loading={loading}
        error={error}
        text={text}
        sender={sender}
      />

      {topNumbers.length > 0 && (
        <RankedBarList
          title="최근 많이 신고된 발신번호"
          icon={Phone}
          colorClass="bg-blue-600"
          items={topNumbers}
        />
      )}
      <OrgGraph graph={graph ?? undefined} />
    </div>
  )
}

export default Analyze
