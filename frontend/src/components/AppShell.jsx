import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  MessageSquareWarning,
  TrendingUp,
  Phone,
  BookOpen,
  Flag,
  Menu,
  X,
} from 'lucide-react'
import Logo from './Logo'

const TAB_ITEMS = [
  { to: '/', label: '분석', icon: MessageSquareWarning, end: true },
  { to: '/trends', label: '트렌드', icon: TrendingUp, end: false },
]

// 하단 탭바(자주 쓰는 2개) 외에 전체 서비스를 모아둔 우측 슬라이드 메뉴
const MENU_ITEMS = [
  { to: '/', label: '문자 분석', icon: MessageSquareWarning, end: true },
  { to: '/lookup', label: '번호·URL 조회', icon: Phone, end: false },
  { to: '/trends', label: '위협 트렌드', icon: TrendingUp, end: false },
  { to: '/guide', label: '스미싱 예방 가이드', icon: BookOpen, end: false },
  { to: '/report', label: '스미싱 신고', icon: Flag, end: false },
]

function AppShell() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <div
      className="relative min-h-screen w-full overflow-x-hidden bg-slate-50"
      style={{ fontFamily: 'Pretendard, system-ui, sans-serif' }}
    >
      {/* 은은한 배경 블롭 — 카드는 다 위에 올라가서 가독성엔 영향 없음 */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[420px] overflow-hidden"
      >
        <div className="absolute -top-24 right-0 h-72 w-72 rounded-full bg-blue-200/40 blur-3xl" />
        <div className="absolute -top-10 left-0 h-64 w-64 rounded-full bg-cyan-200/30 blur-3xl" />
      </div>

      <header className="sticky top-0 z-10 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-4 sm:px-8">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg shadow-sm shadow-blue-500/30">
              <Logo size={32} />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-base font-bold tracking-tight text-slate-900">
                PhishGuard
              </span>
              <span className="text-[11px] font-medium text-slate-400">
                AI 스미싱 탐지
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setIsMenuOpen(true)}
            aria-label="전체 서비스 메뉴 열기"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
          >
            <Menu size={20} strokeWidth={2.25} />
          </button>
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

      {/* 플로팅 필 형태 하단 네비게이션 */}
      <nav className="fixed inset-x-0 bottom-4 z-10 flex justify-center px-4">
        <div className="flex items-center gap-1 rounded-full border border-slate-200 bg-white/90 p-1.5 shadow-lg shadow-slate-900/10 backdrop-blur-md">
          {TAB_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30'
                    : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
                }`
              }
            >
              <Icon size={17} strokeWidth={2.25} />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* 우측 슬라이드 서비스 메뉴 */}
      <div
        onClick={() => setIsMenuOpen(false)}
        aria-hidden="true"
        className={`fixed inset-0 z-30 bg-slate-900/30 transition-opacity ${
          isMenuOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
      />
      <aside
        className={`fixed inset-y-0 right-0 z-40 flex w-72 flex-col gap-2 border-l border-slate-200 bg-white p-5 shadow-2xl shadow-slate-900/10 transition-transform duration-300 ${
          isMenuOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm font-semibold text-slate-700">
            전체 서비스
          </span>
          <button
            type="button"
            onClick={() => setIsMenuOpen(false)}
            aria-label="메뉴 닫기"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-900"
          >
            <X size={18} strokeWidth={2.25} />
          </button>
        </div>

        {MENU_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={() => setIsMenuOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${
                isActive
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-slate-600 hover:bg-slate-100'
              }`
            }
          >
            <Icon size={18} strokeWidth={2.25} />
            {label}
          </NavLink>
        ))}
      </aside>
    </div>
  )
}

export default AppShell
