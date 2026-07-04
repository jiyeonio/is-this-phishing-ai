import { useEffect, useState } from 'react'
import { TrendingUp, MessageSquareText, Link2, Building2 } from 'lucide-react'
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
  top_orgs: [
    { label: '국세청 사칭', count: 33 },
    { label: '경찰청 사칭', count: 27 },
    { label: 'CJ대한통운 사칭', count: 22 },
    { label: '농협은행 사칭', count: 14 },
  ],
}

// 색상은 dataviz 팔레트 검증(라이트 서피스 기준 명도밴드/CVD/대비) 통과한 조합
const SECTIONS = [
  {
    key: 'top_phrases',
    title: '최다 신고 문구',
    icon: MessageSquareText,
    colorClass: 'bg-blue-600',
  },
  {
    key: 'top_urls',
    title: '최다 신고 URL',
    icon: Link2,
    colorClass: 'bg-cyan-600',
  },
  {
    key: 'top_orgs',
    title: '최다 사칭 기관',
    icon: Building2,
    colorClass: 'bg-amber-600',
  },
]

function Trends() {
  const [trends, setTrends] = useState(MOCK_TRENDS)

  useEffect(() => {
    getTrends()
      .then(setTrends)
      .catch((err) => console.error('트렌드 로드 실패:', err))
  }, [])

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <TrendingUp className="text-blue-600" size={22} strokeWidth={2.25} />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            위협 트렌드
          </h1>
        </div>
        <p className="text-sm text-slate-500">
          최근 접수된 신고를 기반으로 자주 등장하는 스미싱 패턴을 집계합니다.
        </p>
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
