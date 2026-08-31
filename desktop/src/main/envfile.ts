export function parseEnv(text: string): Record<string, string> {
  const out: Record<string, string> = {}
  for (const line of text.split(/\r?\n/)) {
    const m = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/.exec(line)
    if (!m || line.trim().startsWith('#')) continue
    let v = m[2]
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'")))
      v = v.slice(1, -1)
    out[m[1]] = v
  }
  return out
}

export function serializeEnv(existing: string, patch: Record<string, string>): string {
  const remaining = { ...patch }
  const lines = existing.split(/\r?\n/)
  if (lines.at(-1) === '') lines.pop()
  const rewritten = lines.map((line) => {
    const m = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=/.exec(line)
    if (m && !line.trim().startsWith('#') && m[1] in remaining) {
      const v = remaining[m[1]]
      delete remaining[m[1]]
      return `${m[1]}=${v}`
    }
    return line
  })
  for (const [k, v] of Object.entries(remaining)) rewritten.push(`${k}=${v}`)
  return rewritten.filter((l, i) => !(i === 0 && l === '' && rewritten.length === 1)).join('\n') + '\n'
}
