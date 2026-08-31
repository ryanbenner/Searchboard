import { BrowserWindow, app, ipcMain, shell } from 'electron'
import { join } from 'node:path'
import { Db } from './db'
import { readProfile, writeProfile } from './profile'
import { RunHistory } from './runs'
import { Runner, buildRunArgs } from './runner'
import { Settings } from './settings'
import { Sync } from './sync'

export function registerIpc(win: BrowserWindow): void {
  const settings = new Settings(join(app.getPath('userData'), 'config.json'))
  const history = new RunHistory(join(app.getPath('userData'), 'runs.json'))
  let db: Db | null = null
  let sync: Sync | null = null
  const send = (ch: string, ...args: unknown[]): void => {
    if (!win.isDestroyed()) win.webContents.send(ch, ...args)
  }

  const ready = (): boolean => settings.validate().length === 0
  const getDb = (): Db => {
    if (!ready()) throw new Error('settings incomplete')
    return (db ??= new Db(join(settings.get().dataRepo, 'seen.sqlite')))
  }
  const getSync = (): Sync => (sync ??= new Sync(settings.get().dataRepo, (s, d) => send('sync:state', s, d)))

  const runner = new Runner({
    onLine: (line, kind) => send('run:line', line, kind),
    onDone: (rec) => {
      const today = new Date().toISOString().slice(0, 10)
      rec.added = getDb().listJobs().filter((j) => j.firstSeen === today).length
      history.add(rec)
      void getSync().commitAndPush(`searchboard run ${today}`)
      send('run:done', rec)
    },
  })

  ipcMain.handle('settings:get', () => ({ config: settings.get(), secrets: settings.secretStatus(), issues: settings.validate() }))
  ipcMain.handle('settings:set', (_e, patch) => {
    settings.set(patch)
    db?.close()
    db = null
    sync = null // paths may have changed
  })
  ipcMain.handle('secrets:set', (_e, patch) => settings.setSecrets(patch))
  ipcMain.handle('jobs:list', () => getDb().listJobs())
  ipcMain.handle('jobs:update', (_e, id, patch) => {
    if (runner.running) throw new Error('run in progress — edits disabled')
    getDb().updateJob(id, patch)
    getSync().scheduleDebouncedPush('searchboard status update')
  })
  ipcMain.handle('jobs:openUrl', (_e, id) => {
    const job = getDb().listJobs().find((j) => j.id === id)
    if (!job) return
    void shell.openExternal(job.url)
    if (job.status === 'New' && !runner.running) {
      getDb().updateJob(id, { status: 'Visited' })
      getSync().scheduleDebouncedPush('searchboard status update')
    }
  })
  ipcMain.handle('profile:get', () => readProfile(join(settings.get().dataRepo, 'profile.yml')))
  ipcMain.handle('profile:set', (_e, p) => {
    writeProfile(join(settings.get().dataRepo, 'profile.yml'), p)
    getSync().scheduleDebouncedPush('searchboard profile update')
  })
  ipcMain.handle('runs:history', () => history.list())
  ipcMain.handle('sync:now', () => getSync().pull())
  ipcMain.handle('run:start', async () => {
    if (runner.running) return { ok: false, error: 'a run is already active' }
    if (!ready()) return { ok: false, error: 'settings incomplete' }
    try {
      const cfg = settings.get()
      db?.close()
      db = null // pipeline writes the file; reopen lazily after
      await getSync().pull() // offline is fine; run continues on local data
      runner.start('uv', buildRunArgs(cfg.dataRepo, cfg.emailOnManualRuns), cfg.codeRepo, settings.readSecrets())
      return { ok: true }
    } catch (e) {
      return { ok: false, error: (e as Error).message }
    }
  })
}
