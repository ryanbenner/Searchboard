export type LineKind = 'cmd' | 'dim' | 'ok' | 'error' | 'plain'

export function classifyLine(line: string): LineKind {
  if (line.startsWith('$ ')) return 'cmd'
  if (/^\[warn\]|^Traceback|Error|error:/.test(line)) return 'error'
  if (/^(raw=|verified=|ranked=|loaded |deduped |--no-email)/.test(line)) return 'dim'
  if (/^(done|wrote |committed )/.test(line)) return 'ok'
  return 'plain'
}

export function parseSummary(lines: string[]): { raw?: number; filtered?: number; ranked?: number } {
  const out: { raw?: number; filtered?: number; ranked?: number } = {}
  for (const l of lines) {
    const m1 = /raw=(\d+) filtered=(\d+)/.exec(l)
    if (m1) {
      out.raw = +m1[1]
      out.filtered = +m1[2]
    }
    const m2 = /ranked=(\d+)/.exec(l)
    if (m2) out.ranked = +m2[1]
  }
  return out
}
