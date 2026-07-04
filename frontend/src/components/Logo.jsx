// 커스텀 로고마크: 방패(보안) + 체크(검증) + 스파클(AI). 라이브러리 아이콘이 아니라 브랜드 전용 SVG.
function Logo({ size = 32, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="PhishGuard 로고"
    >
      <defs>
        <linearGradient
          id="pg-logo-bg"
          x1="2"
          y1="2"
          x2="30"
          y2="30"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0" stopColor="#2563EB" />
          <stop offset="1" stopColor="#0891B2" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#pg-logo-bg)" />
      <path
        d="M16 6L23 9V14.5C23 19.5 20 23.7 16 25C12 23.7 9 19.5 9 14.5V9L16 6Z"
        fill="white"
      />
      <path
        d="M12.5 15.3L14.9 17.7L19.5 12.3"
        stroke="#1E3A8A"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <path
        d="M24 4L25 6.2L27.2 7.2L25 8.2L24 10.4L23 8.2L20.8 7.2L23 6.2Z"
        fill="white"
      />
    </svg>
  )
}

export default Logo
