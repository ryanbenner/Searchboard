export type { JobRow } from '../main/db'
export type { Status } from '../main/statusRules'
export { STATUSES } from '../main/statusRules'
export type { AppConfig, SecretStatus, ValidationIssue } from '../main/settings'
export type { SearchProfile } from '../main/profile'
export type { RunRecord } from '../main/runs'
export type { SyncState } from '../main/sync'
export type { LineKind } from '../main/logclass'
export { classifyLine } from '../main/logclass'

import type { JobRow } from '../main/db'
import type { Status } from '../main/statusRules'
import type { AppConfig, SecretStatus, ValidationIssue } from '../main/settings'
import type { SearchProfile } from '../main/profile'
import type { RunRecord } from '../main/runs'
import type { SyncState } from '../main/sync'
import type { LineKind } from '../main/logclass'

export interface SearchboardApi {
  settingsGet(): Promise<{ config: AppConfig; secrets: SecretStatus; issues: ValidationIssue[] }>
  settingsSet(patch: Partial<AppConfig>): Promise<void>
  secretsSet(patch: Record<string, string>): Promise<void>
  jobsList(): Promise<JobRow[]>
  jobsUpdate(id: string, patch: { status?: Status; notes?: string }): Promise<void>
  jobsOpenUrl(id: string): Promise<void>
  profileGet(): Promise<SearchProfile>
  profileSet(p: SearchProfile): Promise<void>
  runStart(): Promise<{ ok: boolean; error?: string }>
  runsHistory(): Promise<RunRecord[]>
  syncNow(): Promise<SyncState>
  onRunLine(cb: (line: string, kind: LineKind) => void): () => void
  onRunDone(cb: (rec: RunRecord) => void): () => void
  onSyncState(cb: (state: SyncState, detail?: string) => void): () => void
}
