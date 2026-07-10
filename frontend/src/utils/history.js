// "최근 분석 결과" — 백엔드 저장소가 아니라 로컬(localStorage)에만 남기는 개인 기록
const STORAGE_KEY = 'phishguard_recent_analyses'
const MAX_ENTRIES = 5

export function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function addHistoryEntry({ text, sender, level }) {
  const entry = {
    id: `${Date.now()}`,
    sender: sender?.trim() || '번호 없음',
    snippet: text.trim().slice(0, 40),
    level,
    timestamp: Date.now(),
  }
  const next = [entry, ...loadHistory()].slice(0, MAX_ENTRIES)
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  } catch {
    // 저장 실패해도 화면 흐름엔 영향 없게 조용히 무시
  }
  return next
}

export function formatRelativeTime(timestamp) {
  const diffMs = Date.now() - timestamp
  const minutes = Math.floor(diffMs / 60000)
  if (minutes < 1) return '방금 전'
  if (minutes < 60) return `${minutes}분 전`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`
  const days = Math.floor(hours / 24)
  if (days < 2) return '어제'
  return `${days}일 전`
}
