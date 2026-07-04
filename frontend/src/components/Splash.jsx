import Logo from './Logo'

function Splash() {
  return (
    <div
      className="flex min-h-screen w-full flex-col items-center justify-center gap-5 bg-slate-50"
      style={{ fontFamily: 'Pretendard, system-ui, sans-serif' }}
    >
      <div className="relative flex h-20 w-20 items-center justify-center">
        <span className="absolute inset-0 animate-ping rounded-2xl bg-blue-300/40" />
        <div className="relative shadow-lg shadow-blue-500/30 [animation:splash-pop_0.5s_ease-out]">
          <Logo size={64} />
        </div>
      </div>

      <div className="flex flex-col items-center gap-1 [animation:splash-fade-in_0.6s_ease-out_0.15s_both]">
        <span className="text-2xl font-bold tracking-tight text-slate-900">
          PhishGuard
        </span>
        <span className="text-xs font-medium text-slate-400">
          AI 스미싱 탐지 엔진
        </span>
      </div>

      <div className="relative h-1 w-28 overflow-hidden rounded-full bg-slate-200 [animation:splash-fade-in_0.4s_ease-out_0.3s_both]">
        <div className="absolute inset-y-0 w-1/3 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 [animation:splash-loading_0.9s_ease-in-out_infinite]" />
      </div>
    </div>
  )
}

export default Splash
