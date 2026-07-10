// 개발가이드 "신고 문구 템플릿" 그대로
export function buildReportText({ text, sender, urls, riskScore, reasons }) {
  const urlLine = urls?.length ? urls.join(', ') : '없음'
  const reasonLines = reasons?.length
    ? reasons.slice(0, 3).join('\n')
    : '없음'
  const receivedAt = new Date().toLocaleString('ko-KR')

  return `[스미싱 의심 신고]

■ 수신 문자 내용
${text || '(내용 없음)'}

■ 발신번호
${sender || '미상'}

■ 포함된 의심 URL
${urlLine}

■ 신고 사유
PhishGuard AI 분석 결과 위험도 ${riskScore ?? 0}%로 스미싱이 의심됩니다.
${reasonLines}

■ 수신 일시
${receivedAt}`
}
