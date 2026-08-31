import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const run = promisify(execFile)

export type SyncState = 'idle' | 'syncing' | 'conflict' | 'offline'

export class Sync {
  private timer: NodeJS.Timeout | null = null

  constructor(
    private cwd: string,
    private onState: (s: SyncState, detail?: string) => void
  ) {}

  private async git(...args: string[]): Promise<string> {
    const { stdout } = await run('git', args, { cwd: this.cwd })
    return stdout
  }

  private classify(e: unknown): SyncState {
    const msg = String((e as { stderr?: string; message?: string })?.stderr ?? (e as Error)?.message ?? e)
    return /could not resolve host|unable to access|Could not read from remote/i.test(msg) ? 'offline' : 'conflict'
  }

  private async fail(e: unknown): Promise<SyncState> {
    const state = this.classify(e)
    if (state === 'conflict') {
      try {
        await this.git('rebase', '--abort')
      } catch {
        /* not rebasing */
      }
    }
    this.onState(state, String((e as { stderr?: string })?.stderr ?? e))
    return state
  }

  async pull(): Promise<SyncState> {
    this.onState('syncing')
    try {
      await this.git('pull', '--rebase')
      this.onState('idle')
      return 'idle'
    } catch (e) {
      return this.fail(e)
    }
  }

  async commitAndPush(message: string): Promise<SyncState> {
    this.onState('syncing')
    try {
      await this.git('add', '-A')
      const staged = await this.git('diff', '--staged', '--name-only')
      if (staged.trim()) await this.git('commit', '-m', message)
      try {
        await this.git('push')
      } catch (e) {
        if (this.classify(e) === 'offline') throw e
        await this.git('pull', '--rebase')
        await this.git('push')
      }
      this.onState('idle')
      return 'idle'
    } catch (e) {
      return this.fail(e)
    }
  }

  scheduleDebouncedPush(message: string): void {
    if (this.timer) clearTimeout(this.timer)
    this.timer = setTimeout(() => {
      this.timer = null
      void this.commitAndPush(message)
    }, 15_000)
  }
}
