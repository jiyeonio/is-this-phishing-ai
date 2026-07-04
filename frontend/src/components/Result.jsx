import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  ShieldQuestion,
  Building2,
  Flag,
  Sparkles,
} from 'lucide-react'

const LEVEL_STYLES = {
  safe: {
    label: '안전',
    badge: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    bar: 'bg-emerald-500',
    icon: ShieldCheck,
  },
  suspicious: {
    label: '의심',
    badge: 'border-amber-200 bg-amber-50 text-amber-700',
    bar: 'bg-amber-500',
    icon: ShieldAlert,
  },
  danger: {
    label: '위험',
    badge: 'border-red-200 bg-red-50 text-red-700',
    bar: 'bg-red-500',
    icon: ShieldX,
  },
}

// API 응답 필드명이 바뀌면 이 값들만 고치면 됨
const SIGNAL_FIELDS = {
  model: 'model',
  rule: 'rule',
  reputation: 'reputation',
}

const CLUSTER_FIELDS = {
  orgCount: 'org_count',
  reportCount: 'report_count',
}

const SIGNAL_ITEMS = [
  { key: SIGNAL_FIELDS.model, label: '모델' },
  { key: SIGNAL_FIELDS.rule, label: '규칙' },
  { key: SIGNAL_FIELDS.reputation, label: '평판' },
]

const CARD_CLASS = 'rounded-2xl border border-slate-200 bg-white shadow-sm'
const COUNT_UP_MS = 600

// 위험도 %를 0에서 실제 값까지 부드럽게 채워 보여줌 (ease-out)
function useCountUp(target, durationMs) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    let frame
    const start = performance.now()

    const tick = (now) => {
      const progress = Math.min((now - start) / durationMs, 1)
      const eased = 1 - (1 - progress) ** 3
      setValue(Math.round(target * eased))
      if (progress < 1) frame = requestAnimationFrame(tick)
    }

    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [target, durationMs])

  return value
}

function ResultSkeleton() {
  return (
    <div className={`flex flex-col gap-6 p-5 sm:p-8 ${CARD_CLASS}`}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex flex-col gap-2">
          <div className="h-3 w-14 animate-pulse rounded bg-slate-100" />
          <div className="h-9 w-24 animate-pulse rounded bg-slate-100" />
        </div>
        <div className="h-7 w-16 animate-pulse rounded-full bg-slate-100" />
      </div>
      <div className="h-2 w-full animate-pulse rounded-full bg-slate-100" />
      <div className="flex flex-col gap-2">
        <div className="h-3 w-10 animate-pulse rounded bg-slate-100" />
        <div className="h-3 w-5/6 animate-pulse rounded bg-slate-100" />
        <div className="h-3 w-2/3 animate-pulse rounded bg-slate-100" />
      </div>
      <p className="flex items-center justify-center gap-1.5 text-sm">
        <Sparkles size={14} className="flex-shrink-0 text-blue-400" />
        <span
          className="bg-[length:200%_100%] bg-clip-text font-medium text-transparent [animation:ai-shimmer_1.8s_linear_infinite]"
          style={{
            backgroundImage:
              'linear-gradient(90deg, #94a3b8 40%, #1e293b 50%, #94a3b8 60%)',
          }}
        >
          AI가 문자를 분석하고 있어요...
        </span>
      </p>
    </div>
  )
}

function Result({ result, loading, error, text, sender }) {
  const navigate = useNavigate()
  const percent = Math.round((result?.risk_score ?? 0) * 100)
  const animatedPercent = useCountUp(percent, COUNT_UP_MS)

  if (loading) return <ResultSkeleton />

  if (error) {
    return (
      <div
        className={`flex items-start gap-3 border-red-200 bg-red-50 p-6 text-sm text-red-700 ${CARD_CLASS} [animation:card-in_0.3s_ease-out]`}
      >
        <AlertTriangle size={18} className="mt-0.5 flex-shrink-0" />
        <span>{error}</span>
      </div>
    )
  }

  if (!result) {
    return (
      <div
        className={`flex flex-col items-center gap-3 p-10 text-center ${CARD_CLASS}`}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-50 text-slate-300">
          <ShieldQuestion size={24} strokeWidth={1.75} />
        </div>
        <p className="text-sm text-slate-400">
          아직 분석 결과가 없습니다. 문자 내용을 입력하고 분석하기 버튼을
          눌러주세요.
        </p>
      </div>
    )
  }

  const { level, reasons, evidence, signals, cluster } = result
  const levelStyle = LEVEL_STYLES[level] ?? LEVEL_STYLES.suspicious
  const LevelIcon = levelStyle.icon

  return (
    <div
      className={`flex flex-col gap-6 p-5 sm:p-8 ${CARD_CLASS} [animation:card-in_0.35s_ease-out]`}
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm text-slate-400">위험도</p>
          <p
            className="text-4xl font-extrabold text-slate-900"
            style={{ fontVariantNumeric: 'tabular-nums' }}
          >
            {animatedPercent}%
          </p>
        </div>
        <span
          className={`flex items-center gap-1.5 rounded-full border px-4 py-1.5 text-sm font-semibold [animation:badge-pop_0.3s_ease-out] ${levelStyle.badge}`}
        >
          <LevelIcon size={15} strokeWidth={2.25} />
          {levelStyle.label}
        </span>
      </div>

      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full transition-all duration-500 ${levelStyle.bar}`}
          style={{ width: `${percent}%` }}
        />
      </div>

      {reasons?.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium text-slate-700">근거</p>
          <ul className="flex flex-col gap-1.5">
            {reasons.map((reason, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-slate-600"
              >
                <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-slate-300" />
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {evidence?.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium text-slate-700">탐지 증거</p>
          <div className="flex flex-wrap gap-2">
            {evidence.map((e, i) => (
              <span
                key={i}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600"
              >
                <span className="font-semibold text-slate-400">{e.type}</span>
                {' · '}
                {e.detail}
              </span>
            ))}
          </div>
        </div>
      )}

      {signals && (
        <div className="flex flex-col gap-3">
          <p className="text-sm font-medium text-slate-700">
            신호 분석 (투명성)
          </p>
          {SIGNAL_ITEMS.map(({ key, label }) => {
            const value = signals[key]
            if (value == null) return null
            const signalPercent = Math.round(value * 100)
            return (
              <div key={key} className="flex flex-col gap-1">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>{label}</span>
                  <span>{signalPercent}%</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-blue-500 transition-all duration-500"
                    style={{ width: `${signalPercent}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}

      {cluster && (
        <div className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
          <Building2 size={16} className="flex-shrink-0 text-slate-400" />
          조직 {cluster[CLUSTER_FIELDS.orgCount]}개 연결, 신고{' '}
          {cluster[CLUSTER_FIELDS.reportCount]}건
        </div>
      )}

      <button
        type="button"
        onClick={() => navigate('/report', { state: { text, sender, result } })}
        className="flex items-center justify-center gap-2 rounded-xl border border-red-200 bg-red-50 px-6 py-3 text-sm font-semibold text-red-700 transition hover:bg-red-100 active:bg-red-200"
      >
        <Flag size={16} strokeWidth={2.25} />
        신고하기
      </button>
    </div>
  )
}

export default Result
