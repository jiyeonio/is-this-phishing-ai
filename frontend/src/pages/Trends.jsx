import { useEffect, useState } from 'react'
import {
  TrendingUp,
  MessageSquareText,
  Link2,
  AlertTriangle,
} from 'lucide-react'
import { getTrends } from '../api/client'
import RankedBarList from '../components/RankedBarList'

// getTrends() 실패 시(백엔드 미준비) 폴백으로 쓰는 목업 — OrgGraph 목업과 동일 시나리오
const MOCK_TRENDS = {
  top_phrases: [
    { label: '계좌 정지 안내', count: 42 },
    { label: '택배 배송 조회', count: 35 },
    { label: '환급금 조회', count: 28 },
    { label: '본인인증 필요', count: 19 },
  ],
  top_urls: [
    { label: 'phish-bank.kr', count: 37 },
    { label: 'bit.ly/abcxyz', count: 31 },
    { label: 'gov-refund.net', count: 24 },
    { label: 'short.url/kk22', count: 15 },
  ],
}

const SECTIONS = [
  {
    key: 'top_phrases',
    title: '최다 신고 문구',
    icon: MessageSquareText,
    colorClass: 'bg-slate-900',
  },
  {
    key: 'top_urls',
    title: '최다 신고 URL',
    icon: Link2,
    colorClass: 'bg-slate-900',
  },
]

const sumCounts = (items) => items?.reduce((sum, item) => sum + item.count, 0) ?? 0

function Trends() {
  const [trends, setTrends] = useState(MOCK_TRENDS)
  const [loadError, setLoadError] = useState(null)

  useEffect(() => {
    getTrends()
      .then((data) => {
        setTrends(data)
        setLoadError(null)
      })
      .catch((err) => {
        console.error('트렌드 로드 실패:', err)
        setLoadError('실시간 데이터를 불러오지 못해 예시 데이터를 보여드립니다.')
      })
  }, [])

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <TrendingUp className="text-slate-900" size={22} strokeWidth={2.25} />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            위협 트렌드
          </h1>
        </div>
        <p className="text-sm text-slate-500">
          최근 접수된 신고를 기반으로 자주 등장하는 스미싱 패턴을 집계합니다.
        </p>
      </div>

      {loadError && (
        <div className="flex items-start gap-3 rounded-2xl border border-slate-300 bg-slate-50 p-4 text-sm text-slate-700 [animation:card-in_0.3s_ease-out]">
          <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
          <span>{loadError}</span>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-center shadow-sm">
          <p className="text-xl font-bold text-slate-900">
            {(
              sumCounts(trends.top_phrases) + sumCounts(trends.top_urls)
            ).toLocaleString()}
          </p>
          <p className="text-xs text-slate-400">총 신고</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-center shadow-sm">
          <p className="text-xl font-bold text-slate-900">
            {trends.top_urls?.length ?? 0}
          </p>
          <p className="text-xs text-slate-400">위험 도메인</p>
        </div>
      </div>

      {SECTIONS.map(({ key, title, icon, colorClass }, i) => (
        <RankedBarList
          key={key}
          title={title}
          icon={icon}
          colorClass={colorClass}
          items={trends[key] ?? []}
          delayMs={i * 80}
        />
      ))}
    </div>
  )
}

export default Trends
