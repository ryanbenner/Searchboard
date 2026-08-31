import { existsSync, readFileSync, writeFileSync } from 'node:fs'

export interface RunRecord {
  id: string
  startedAt: string
  durationMs: number
  exitCode: number | null
  found: number | null
  added: number | null
  log: string
}

export class RunHistory {
  constructor(private jsonPath: string) {}

  list(): RunRecord[] {
    if (!existsSync(this.jsonPath)) return []
    try {
      const parsed = JSON.parse(readFileSync(this.jsonPath, 'utf8'))
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }

  add(rec: RunRecord): void {
    writeFileSync(this.jsonPath, JSON.stringify([rec, ...this.list()].slice(0, 50), null, 2) + '\n')
  }
}
