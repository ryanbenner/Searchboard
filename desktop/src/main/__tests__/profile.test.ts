import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { parse } from 'yaml'
import { expect, test } from 'vitest'
import { readProfile, writeProfile } from '../profile'

const SAMPLE = `name: Ryan
email: r@x.com
target_roles:
  - Full-stack Engineer
seniority:
  years_experience: 2
  bands: [junior]
location:
  remote_ok: true
  remote_country: US
  onsite_metros: [NYC]
  exclude_metros: []
compensation:
  min_usd: 120000
  target_usd: 150000
skills:
  strong: [react]
exclusions:
  industries: [crypto]
  companies: []
  keywords: [clearance]
highlights: []
`

function tmpYml(): string {
  const p = join(mkdtempSync(join(tmpdir(), 'sbp-')), 'profile.yml')
  writeFileSync(p, SAMPLE)
  return p
}

test('readProfile maps the five edited fields', () => {
  expect(readProfile(tmpYml())).toEqual({
    titles: ['Full-stack Engineer'],
    excludeKeywords: ['clearance'],
    locations: ['NYC'],
    remoteOnly: true,
    minSalary: 120000,
  })
})

test('writeProfile updates edited fields and preserves everything else', () => {
  const p = tmpYml()
  writeProfile(p, {
    titles: ['Backend Engineer'],
    excludeKeywords: [],
    locations: ['NYC', 'Boston'],
    remoteOnly: false,
    minSalary: 130000,
  })
  const doc = parse(readFileSync(p, 'utf8'))
  expect(doc.target_roles).toEqual(['Backend Engineer'])
  expect(doc.location.onsite_metros).toEqual(['NYC', 'Boston'])
  expect(doc.location.remote_ok).toBe(false)
  expect(doc.location.remote_country).toBe('US')
  expect(doc.compensation.min_usd).toBe(130000)
  expect(doc.compensation.target_usd).toBe(150000)
  expect(doc.seniority.years_experience).toBe(2)
  expect(doc.name).toBe('Ryan')
})
