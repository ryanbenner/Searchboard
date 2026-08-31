import { contextBridge, ipcRenderer } from 'electron'
import type { SearchboardApi } from '../shared/types'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const on = (ch: string) => (cb: (...args: any[]) => void) => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const h = (_e: unknown, ...args: any[]): void => cb(...args)
  ipcRenderer.on(ch, h)
  return () => ipcRenderer.removeListener(ch, h)
}

const api: SearchboardApi = {
  settingsGet: () => ipcRenderer.invoke('settings:get'),
  settingsSet: (patch) => ipcRenderer.invoke('settings:set', patch),
  secretsSet: (patch) => ipcRenderer.invoke('secrets:set', patch),
  jobsList: () => ipcRenderer.invoke('jobs:list'),
  jobsUpdate: (id, patch) => ipcRenderer.invoke('jobs:update', id, patch),
  jobsOpenUrl: (id) => ipcRenderer.invoke('jobs:openUrl', id),
  profileGet: () => ipcRenderer.invoke('profile:get'),
  profileSet: (p) => ipcRenderer.invoke('profile:set', p),
  runStart: () => ipcRenderer.invoke('run:start'),
  runsHistory: () => ipcRenderer.invoke('runs:history'),
  syncNow: () => ipcRenderer.invoke('sync:now'),
  onRunLine: on('run:line'),
  onRunDone: on('run:done'),
  onSyncState: on('sync:state'),
}

contextBridge.exposeInMainWorld('searchboard', api)
