import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  RotateCw,
  ShieldCheck,
  ExternalLink,
  CheckCircle2,
} from 'lucide-react'
import { report, getGraph } from '../api/client'
import { buildReportText } from '../utils/buildReportText'
import OrgGraph from '../components/OrgGraph'

const CARD_CLASS =
  'rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-8'

const OFFICIAL_REPORT_TARGETS = [
  {
    key: 'kisa',
    label: 'KISA 스팸신고로 이동',
    url: 'https://spam.kisa.or.kr',
  },
]

// urls 필드는 B(백엔드) 작업 완료 전까지 없을 수 있음 → evidence의 url 타입으로 폴백
function extractUrls(result) {
  if (result?.urls?.length) return result.urls
  return (
    result?.evidence
      ?.filter((e) => e.type === 'url')
      .map((e) => e.detail) ?? []
  )
}

function Report() {
  const location = useLocation()
  const navigate = useNavigate()
  const result = location.state?.result

  const [text, setText] = useState(location.state?.text ?? '')
  const [sender, setSender] = useState(location.state?.sender ?? '')
  const [previewText, setPreviewText] = useState(() =>
    buildReportText({
      text: location.state?.text ?? '',
      sender: location.state?.sender ?? '',
      urls: extractUrls(result),
      riskScore: Math.round((result?.risk_score ?? 0) * 100),
      reasons: result?.reasons,
    }),
  )
  const [submitting, setSubmitting] = useState(false)
  const [status, setStatus] = useState(null)
  const [graph, setGraph] = useState(null)

  const regeneratePreview = () => {
    setPreviewText(
      buildReportText({
        text,
        sender,
        urls: extractUrls(result),
        riskScore: Math.round((result?.risk_score ?? 0) * 100),
        reasons: result?.reasons,
      }),
    )
  }

  const handleReportToDb = async () => {
    setSubmitting(true)
    setStatus(null)
    try {
      await report(text, sender)
      setStatus('신고 완료, 평판DB 반영됨')

      try {
        const data = await getGraph()
        setGraph(data)
      } catch (err) {
        console.error('그래프 새로고침 실패:', err)
      }
    } catch (err) {
      console.error('신고 요청 실패:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleOfficialReport = async (url) => {
    try {
      await navigator.clipboard.writeText(previewText)
    } catch (err) {
      console.error('신고 문구 복사 실패:', err)
    }
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="flex flex-col gap-8">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 self-start text-sm text-slate-500 transition hover:text-slate-800"
      >
        <ArrowLeft size={15} strokeWidth={2.25} />
        돌아가기
      </button>

      <div className="flex flex-col gap-1.5">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          스미싱 신고
        </h1>
        <p className="text-sm text-slate-500">
          내용을 확인·수정한 뒤 PhishGuard DB 또는 공식 신고처로 접수할 수
          있습니다.
        </p>
      </div>

      <div className={CARD_CLASS}>
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
            onClick={regeneratePreview}
            className="flex items-center gap-1.5 self-start text-sm font-medium text-blue-600 transition hover:text-blue-500"
          >
            <RotateCw size={14} strokeWidth={2.25} />
            신고 문구 미리보기 새로고침
          </button>
        </div>
      </div>

      <div className={CARD_CLASS}>
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-slate-700">
              신고 문구 미리보기 (수정 가능)
            </label>
            <textarea
              value={previewText}
              onChange={(e) => setPreviewText(e.target.value)}
              rows={12}
              className="w-full resize-none whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 font-mono text-sm text-slate-800 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={handleReportToDb}
              disabled={submitting}
              className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:from-blue-500 hover:to-cyan-500 active:scale-[0.98] active:from-blue-700 active:to-cyan-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100"
            >
              <ShieldCheck size={16} strokeWidth={2.25} />
              {submitting ? '제출 중...' : 'PhishGuard에 신고'}
            </button>

            {OFFICIAL_REPORT_TARGETS.map(({ key, label, url }) => (
              <button
                key={key}
                type="button"
                onClick={() => handleOfficialReport(url)}
                className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
              >
                <ExternalLink size={15} strokeWidth={2.25} />
                {label}
              </button>
            ))}
          </div>

          {status && (
            <p className="flex items-center gap-1.5 text-sm font-medium text-emerald-600">
              <CheckCircle2 size={15} strokeWidth={2.25} />
              {status}
            </p>
          )}
        </div>
      </div>

      {graph && <OrgGraph graph={graph} />}
    </div>
  )
}

export default Report
