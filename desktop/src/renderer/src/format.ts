const k = (n: number): string => `${Math.round(n / 1000)}`

export function fmtSalary(min: number | null, max: number | null): string {
  if (min && max) return `$${k(min)}–${k(max)}k`
  if (min) return `$${k(min)}k+`
  if (max) return `up to $${k(max)}k`
  return '—'
}

export function fmtAgo(isoDate: string | null): string {
  if (!isoDate) return '—'
  const days = Math.floor((Date.now() - new Date(isoDate + 'T00:00:00Z').getTime()) / 864e5)
  return days <= 0 ? 'today' : `${days}d`
}

export function fmtDuration(ms: number): string {
  const s = Math.round(ms / 1000)
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`
}
