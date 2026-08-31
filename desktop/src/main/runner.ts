import { spawn } from 'node:child_process'
import { join } from 'node:path'
import { classifyLine, parseSummary, type LineKind } from './logclass'
import type { RunRecord } from './runs'

export function buildRunArgs(dataRepo: string, emailOnManualRuns: boolean): string[] {
  const args = ['run', 'python', '-m', 'searchboard', 'run',
    '--profile', join(dataRepo, 'profile.yml'), '--data-dir', dataRepo]
  if (!emailOnManualRuns) args.push('--no-email')
  return args
}

export interface RunnerEvents {
  onLine: (line: string, kind: LineKind) => void
  onDone: (rec: RunRecord) => void
}

export class Runner {
  private proc: ReturnType<typeof spawn> | null = null

  constructor(private events: RunnerEvents) {}

  get running(): boolean {
    return this.proc !== null
  }

  start(exe: string, args: string[], cwd: string, env: Record<string, string>): void {
    if (this.proc) throw new Error('a run is already active')
    const startedAt = new Date().toISOString()
    const t0 = Date.now()
    const all: string[] = []
    const emitChunk = (buf: Buffer): void => {
      for (const line of buf.toString().split(/\r?\n/)) {
        if (!line.trim()) continue
        all.push(line)
        this.events.onLine(line, classifyLine(line))
      }
    }
    this.proc = spawn(exe, args, { cwd, env: { ...process.env, ...env } })
    this.proc.stdout!.on('data', emitChunk)
    this.proc.stderr!.on('data', emitChunk)
    const finish = (exitCode: number | null, extra?: string): void => {
      if (extra) {
        all.push(extra)
        this.events.onLine(extra, 'error')
      }
      this.proc = null
      const sum = parseSummary(all)
      this.events.onDone({
        id: startedAt,
        startedAt,
        durationMs: Date.now() - t0,
        exitCode,
        found: sum.filtered ?? sum.raw ?? null,
        added: null,
        log: all.join('\n'),
      })
    }
    this.proc.on('error', (e) => finish(null, `failed to start: ${e.message}`))
    this.proc.on('close', (code) => finish(code))
  }
}
