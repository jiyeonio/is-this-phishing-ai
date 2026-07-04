import { useEffect, useState } from 'react'

function RankedBarList({ title, icon: Icon, colorClass, items, delayMs = 0 }) {
  const maxCount = Math.max(...items.map((item) => item.count), 1)
  const [grown, setGrown] = useState(false)

  // 마운트 직후 0% → 목표 %로 성장시켜서 막대가 자라나는 느낌을 줌
  useEffect(() => {
    const frame = requestAnimationFrame(() => setGrown(true))
    return () => cancelAnimationFrame(frame)
  }, [])

  return (
    <div
      className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-8 [animation:card-in_0.35s_ease-out_both]"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <div className="flex items-center gap-2">
        <Icon size={16} className="text-slate-400" strokeWidth={2.25} />
        <p className="text-sm font-medium text-slate-700">{title}</p>
      </div>
      <div className="flex flex-col gap-3">
        {items.map((item) => {
          const percent = Math.round((item.count / maxCount) * 100)
          return (
            <div
              key={item.label}
              className="flex flex-col gap-1"
              title={`${item.label}: ${item.count.toLocaleString()}건`}
            >
              <div className="flex items-center justify-between gap-3 text-xs text-slate-500">
                <span className="truncate">{item.label}</span>
                <span className="flex-shrink-0 font-semibold text-slate-800">
                  {item.count.toLocaleString()}건
                </span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full rounded-r-full transition-all duration-700 ease-out ${colorClass}`}
                  style={{ width: grown ? `${percent}%` : '0%' }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default RankedBarList
