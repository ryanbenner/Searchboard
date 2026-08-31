import { expect, test } from 'vitest'
import { sortJobs } from '../sortJobs'
import type { JobRow } from '../../../shared/types'

const day = (n: number): string => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10)
const j = (id: string, score: number | null, ageDays: number, location: string | null = null): JobRow =>
  ({ id, score, firstSeen: day(ageDays), location }) as JobRow

test('rank: score desc, nulls last, newer breaks ties', () => {
  const out = sortJobs([j('a', 50, 0), j('b', null, 0), j('c', 90, 5), j('d', 50, 3)], 'rank')
  expect(out.map((x) => x.id)).toEqual(['c', 'a', 'd', 'b'])
})

test('recent: newest first, score breaks ties', () => {
  const out = sortJobs([j('a', 50, 2), j('b', 90, 2), j('c', 10, 0)], 'recent')
  expect(out.map((x) => x.id)).toEqual(['c', 'b', 'a'])
})

test('rank-recent: recency drags down stale high scores', () => {
  // 90 from 20 days ago (90 - 2*20 = 50) loses to 70 from today (70)
  const out = sortJobs([j('a', 90, 20), j('b', 70, 0)], 'rank-recent')
  expect(out.map((x) => x.id)).toEqual(['b', 'a'])
})

test('location: alphabetical, unknown last', () => {
  const out = sortJobs([j('a', 50, 0, 'NYC'), j('b', 50, 0, null), j('c', 50, 0, 'Austin')], 'location')
  expect(out.map((x) => x.id)).toEqual(['c', 'a', 'b'])
})

test('does not mutate the input array', () => {
  const input = [j('a', 10, 0), j('b', 90, 0)]
  sortJobs(input, 'rank')
  expect(input.map((x) => x.id)).toEqual(['a', 'b'])
})
