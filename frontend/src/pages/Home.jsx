import { useNavigate } from 'react-router-dom'
import { ScanSearch, Network, TrendingUp } from 'lucide-react'
import Logo from '../components/Logo'
import NetworkHero from '../components/NetworkHero'

const FEATURES = [
  {
    icon: ScanSearch,
    title: 'AI 위험도 분석',
    desc: '문자 내용과 발신번호를 조합해 피싱 위험도를 0~100 점수로 즉시 산출합니다.',
  },
  {
    icon: Network,
    title: '조직 그래프 인텔리전스',
    desc: '신고된 번호·도메인의 연결 네트워크를 시각화해 피싱 조직 전체 구조를 파악합니다.',
  },
  {
    icon: TrendingUp,
    title: '실시간 트렌드 대시보드',
    desc: '최다 신고 도메인·문구·사칭 기관을 실시간 차트로 확인합니다.',
  },
]

function Home() {
  const navigate = useNavigate()

  return (
    <div className="relative flex flex-col gap-8">
      {/* 화면 전체를 떠다니는 노드 배경 — 박스에 갇히지 않고 헤더/하단 탭 아래로 자연스럽게 이어짐 */}
      <NetworkHero className="fixed inset-0 z-0 h-full w-full" />

      <div className="relative z-10 flex flex-col gap-3">
        <Logo size={44} />
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
          스미싱을 꿰뚫는
          <br />
          AI 인텔리전스
        </h1>
        <p className="text-sm text-slate-500">
          하이브리드 탐지 엔진이 문자 속 위협을 실시간으로 분석하고 조직
          연결망까지 추적합니다.
        </p>
      </div>

      <button
        type="button"
        onClick={() => navigate('/analyze')}
        className="relative z-10 flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-6 py-3.5 text-base font-semibold text-white shadow-lg shadow-slate-900/20 transition hover:bg-slate-800 active:scale-[0.98]"
      >
        지금 문자 분석 시작
      </button>

      <div className="relative z-10 flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-slate-700">핵심 기능</h2>
        {FEATURES.map(({ icon: Icon, title, desc }) => (
          <div
            key={title}
            className="flex items-start gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-700">
              <Icon size={20} strokeWidth={2.25} />
            </div>
            <div className="flex flex-1 flex-col gap-0.5">
              <p className="font-semibold text-slate-900">{title}</p>
              <p className="text-sm text-slate-500">{desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Home
