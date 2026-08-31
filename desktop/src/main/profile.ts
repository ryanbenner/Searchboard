import { readFileSync, writeFileSync } from 'node:fs'
import { parseDocument } from 'yaml'

export interface SearchProfile {
  titles: string[]
  excludeKeywords: string[]
  locations: string[]
  remoteOnly: boolean
  minSalary: number
}

export function readProfile(ymlPath: string): SearchProfile {
  const d = parseDocument(readFileSync(ymlPath, 'utf8'))
  const js = d.toJS()
  return {
    titles: js.target_roles ?? [],
    excludeKeywords: js.exclusions?.keywords ?? [],
    locations: js.location?.onsite_metros ?? [],
    remoteOnly: js.location?.remote_ok ?? false,
    minSalary: js.compensation?.min_usd ?? 0,
  }
}

export function writeProfile(ymlPath: string, p: SearchProfile): void {
  const d = parseDocument(readFileSync(ymlPath, 'utf8'))
  d.setIn(['target_roles'], p.titles)
  d.setIn(['exclusions', 'keywords'], p.excludeKeywords)
  d.setIn(['location', 'onsite_metros'], p.locations)
  d.setIn(['location', 'remote_ok'], p.remoteOnly)
  d.setIn(['compensation', 'min_usd'], p.minSalary)
  writeFileSync(ymlPath, d.toString())
}
