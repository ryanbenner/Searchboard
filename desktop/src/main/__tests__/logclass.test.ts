import { expect, test } from 'vitest'
import { classifyLine, parseSummary } from '../logclass'

test('classification heuristics', () => {
  expect(classifyLine('$ uv run python -m searchboard run')).toBe('cmd')
  expect(classifyLine('[warn] Greenhouse failed: 503')).toBe('error')
  expect(classifyLine('Traceback (most recent call last):')).toBe('error')
  expect(classifyLine('raw=120 filtered=34')).toBe('dim')
  expect(classifyLine('done in 33s')).toBe('ok')
  expect(classifyLine('verified=30 (dropped 4 dead links)')).toBe('dim')
  expect(classifyLine('loading greenhouse …')).toBe('plain')
})

test('parseSummary pulls counts from pipeline stderr', () => {
  expect(
    parseSummary(['raw=120 filtered=34', 'verified=30 (dropped 4 dead links)', 'ranked=30 digest=6 all_top=30'])
  ).toEqual({ raw: 120, filtered: 34, ranked: 30 })
})
