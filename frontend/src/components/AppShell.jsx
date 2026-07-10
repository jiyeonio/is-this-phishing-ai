import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Home as HomeIcon,
  MessageSquareWarning,
  Network,
  TrendingUp,
  ChevronLeft,
} from 'lucide-react'
import Logo from './Logo'

// 와이어프레임 기준: 하단 4탭이 유일한 1차 내비게이션 (햄버거 메뉴 없음)
const TAB_ITEMS = [
  { to: '/', label: '홈', icon: HomeIcon, end: true },
  { to: '/analyze', label: '분석', icon: MessageSquareWarning, end: false },
  { to: '/graph', label: '그래프', icon: Network, end: false },
  { to: '/trends', label: '트렌드', icon: TrendingUp, end: false },
]

// 탭에 없는 화면(신고 등)은 뒤로가기 헤더로 진입 — 어느 경로가 "메인 탭"인지 여기서 판단
const isTabRoute = (pathname) => TAB_ITEMS.some((t) => t.to === pathname)

function AppShell() {
  const navigate = useNavigate()
  const location = useLocation()
  const showBack = !isTabRoute(location.pathname)

  return (
    <div
      className="relative min-h-screen w-full overflow-x-hidden bg-slate-50"
      style={{ fontFamily: 'Pretendard, system-ui, sans-serif' }}
    >
      <header className="sticky top-0 z-10 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-2xl items-center gap-3 px-4 py-4 sm:px-8">
          {showBack ? (
            <>
              <button
                type="button"
                onClick={() => navigate(-1)}
                aria-label="뒤로 가기"
                className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
              >
                <ChevronLeft size={20} strokeWidth={2.25} />
              </button>
              <span className="text-base font-bold text-slate-900">
                PhishGuard
              </span>
            </>
          ) : (
            <div className="flex items-center gap-2.5">
              <Logo size={32} />
              <div className="flex flex-col leading-none">
                <span className="text-base font-bold tracking-tight text-slate-900">
                  PhishGuard
                </span>
                <span className="text-[11px] font-medium text-slate-400">
                  AI 스미싱 탐지
                </span>
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="relative mx-auto max-w-2xl px-4 py-10 pb-28 sm:px-8 sm:py-14 sm:pb-28">
        <Outlet />
      </main>

      <footer className="relative mx-auto hidden max-w-2xl px-4 pb-28 sm:block sm:px-8">
        <p className="text-xs leading-relaxed text-slate-400">
          PhishGuard의 분석 결과는 참고용 AI 판단이며 법적 효력이 없습니다. 실제
          피해가 의심되면 공식 신고 기관을 통해 확인해주세요.
        </p>
      </footer>

      {/* 하단 4탭 내비게이션 */}
      <nav className="fixed inset-x-0 bottom-0 z-10 border-t border-slate-200 bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-2xl items-stretch justify-around px-2">
          {TAB_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex flex-1 flex-col items-center gap-1 py-2.5 text-xs font-medium transition ${
                  isActive ? 'text-slate-900' : 'text-slate-400 hover:text-slate-600'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`flex h-9 w-9 items-center justify-center rounded-xl transition ${
                      isActive ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-400'
                    }`}
                  >
                    <Icon size={19} strokeWidth={2.25} />
                  </span>
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}

export default AppShell
