import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import type { JobRow, RunRecord, SyncState } from '../../shared/types'
import { Sidebar } from './components/Sidebar'
import { Jobs } from './screens/Jobs'
import { Overview } from './screens/Overview'
import { Runs } from './screens/Runs'
import { Search } from './screens/Search'
import { Settings } from './screens/Settings'

export type Screen = 'overview' | 'jobs' | 'search' | 'runs' | 'settings'

export interface AppShell {
  screen: Screen
  setScreen(s: Screen): void
  jobs: JobRow[]
  refreshJobs(): Promise<void>
  running: boolean
  lastRun: RunRecord | null
  startRun(): Promise<void>
  syncState: SyncState
  syncDetail?: string
  settingsOk: boolean
  refreshSettings(): Promise<void>
  selectedId: string | null
  setSelectedId(id: string | null): void
}

export const Shell = createContext<AppShell>(null as never)

export default function App(): React.JSX.Element {
  const [screen, setScreen] = useState<Screen>('overview')
  const [jobs, setJobs] = useState<JobRow[]>([])
  const [running, setRunning] = useState(false)
  const [lastRun, setLastRun] = useState<RunRecord | null>(null)
  const [syncState, setSyncState] = useState<SyncState>('idle')
  const [syncDetail, setSyncDetail] = useState<string>()
  const [settingsOk, setSettingsOk] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const refreshJobs = useCallback(async () => {
    try {
      setJobs(await window.searchboard.jobsList())
    } catch {
      setJobs([])
    }
  }, [])
  const refreshSettings = useCallback(async () => {
    const { issues } = await window.searchboard.settingsGet()
    const ok = issues.length === 0
    setSettingsOk(ok)
    if (ok) await refreshJobs()
    else setScreen('settings')
  }, [refreshJobs])

  useEffect(() => {
    void refreshSettings()
    void window.searchboard.runsHistory().then((h) => setLastRun(h[0] ?? null))
    void window.searchboard.syncNow()
    const offDone = window.searchboard.onRunDone((rec) => {
      setRunning(false)
      setLastRun(rec)
      void refreshJobs()
    })
    const offSync = window.searchboard.onSyncState((s, d) => {
      setSyncState(s)
      setSyncDetail(d)
    })
    return () => {
      offDone()
      offSync()
    }
  }, [refreshJobs, refreshSettings])

  const startRun = useCallback(async () => {
    const res = await window.searchboard.runStart()
    if (res.ok) {
      setRunning(true)
      setScreen('runs')
    } else setSyncDetail(res.error)
  }, [])

  const shell = useMemo(
    () => ({ screen, setScreen, jobs, refreshJobs, running, lastRun, startRun, syncState, syncDetail, settingsOk, refreshSettings, selectedId, setSelectedId }),
    [screen, jobs, running, lastRun, startRun, syncState, syncDetail, settingsOk, refreshSettings, refreshJobs, selectedId]
  )

  const Body = { overview: Overview, jobs: Jobs, search: Search, runs: Runs, settings: Settings }[settingsOk ? screen : 'settings']
  return (
    <Shell.Provider value={shell}>
      <div className="app">
        <Sidebar />
        <main className="main">
          <Body />
        </main>
      </div>
    </Shell.Provider>
  )
}
