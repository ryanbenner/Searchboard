import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { expect, test } from 'vitest'
import { RunHistory } from '../runs'

const rec = (id: string) => ({ id, startedAt: id, durationMs: 1000, exitCode: 0, found: 3, added: 1, log: 'x' })

test('add + list round-trips through the json file, newest first, capped at 50', () => {
  const p = join(mkdtempSync(join(tmpdir(), 'sbr-')), 'runs.json')
  const h = new RunHistory(p)
  for (let i = 0; i < 55; i++) h.add(rec(`2026-08-28T07:00:${String(i).padStart(2, '0')}`))
  const again = new RunHistory(p)
  expect(again.list()).toHaveLength(50)
  expect(again.list()[0].id > again.list()[1].id).toBe(true)
})
