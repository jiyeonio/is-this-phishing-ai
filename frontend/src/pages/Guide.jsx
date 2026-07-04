import {
  BookOpen,
  Link2Off,
  KeyRound,
  PhoneOff,
  ShieldQuestion,
  ExternalLink,
} from 'lucide-react'

const CARD_CLASS =
  'flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6'

const TIPS = [
  {
    icon: Link2Off,
    title: '출처가 불분명한 링크는 누르지 않기',
    body: '단축 URL(bit.ly 등)이나 낯선 도메인은 클릭 대신 검색으로 공식 사이트를 직접 찾아 확인하세요.',
  },
  {
    icon: KeyRound,
    title: '금융기관은 문자로 인증번호·비밀번호를 요구하지 않음',
    body: '계좌 정지, 카드 잠금 등 긴급성을 강조하며 개인정보·인증번호 입력을 유도하면 100% 스미싱입니다.',
  },
  {
    icon: PhoneOff,
    title: '이미 링크를 눌렀다면 즉시 조치',
    body: '기기를 비행기 모드로 전환 후 백신 검사 → 공인인증서·계좌 비밀번호 변경 → 통신사 소액결제 차단 순으로 대응하세요.',
  },
  {
    icon: ShieldQuestion,
    title: '의심되면 PhishGuard로 먼저 확인',
    body: '문자 내용을 붙여넣어 위험도를 분석하고, 실제 피싱으로 확인되면 신고까지 한 번에 진행할 수 있습니다.',
  },
]

const OFFICIAL_LINKS = [
  { label: 'KISA 불법스팸대응센터', url: 'https://spam.kisa.or.kr' },
]

function Guide() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <BookOpen className="text-blue-600" size={22} strokeWidth={2.25} />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            스미싱 예방 가이드
          </h1>
        </div>
        <p className="text-sm text-slate-500">
          자주 발생하는 스미싱 수법과 대처법을 미리 알아두세요.
        </p>
      </div>

      {TIPS.map(({ icon: Icon, title, body }, i) => (
        <div
          key={title}
          className={`${CARD_CLASS} [animation:card-in_0.35s_ease-out_both]`}
          style={{ animationDelay: `${i * 60}ms` }}
        >
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
            <Icon size={18} strokeWidth={2.25} />
          </div>
          <div className="flex flex-col gap-1 text-sm">
            <p className="font-semibold text-slate-800">{title}</p>
            <p className="text-slate-500">{body}</p>
          </div>
        </div>
      ))}

      <div className={`${CARD_CLASS} flex-col gap-3`}>
        <p className="text-sm font-medium text-slate-700">공식 신고처</p>
        {OFFICIAL_LINKS.map(({ label, url }) => (
          <a
            key={url}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-sm text-blue-600 transition hover:text-blue-500"
          >
            <ExternalLink size={14} strokeWidth={2.25} />
            {label}
          </a>
        ))}
      </div>
    </div>
  )
}

export default Guide
