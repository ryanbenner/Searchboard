import { expect, test } from 'vitest'
import { sortJobs } from '../sortJobs'
import type { JobRow } from '../../../shared/types'

const day = (n: number): string => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10)
const j = (id: string, score: number | null, postedDaysAgo: number | null, opts: Partial<JobRow> = {}): JobRow =>
  ({ id, score, postedAt: postedDaysAgo == null ? null : day(postedDaysAgo), firstSeen: day(40), location: null, title: id, ...opts }) as JobRow

test('rank: score desc, nulls last, most recently posted breaks ties', () => {
  const out = sortJobs([j('a', 50, 5), j('b', null, 0), j('c', 90, 5), j('d', 50, 1)], 'rank')
  expect(out.map((x) => x.id)).toEqual(['c', 'd', 'a', 'b'])
})

test('recent: most recently posted first, rank is ignored', () => {
  const out = sortJobs([j('a', 90, 2, { title: 'zeta' }), j('b', 10, 0), j('c', 50, 2, { title: 'alpha' })], 'recent')
  expect(out.map((x) => x.id)).toEqual(['b', 'c', 'a'])
})

test('recent falls back to first-seen when posted date is unknown', () => {
  const out = sortJobs([j('a', 50, 5), j('b', 50, null, { firstSeen: day(1) })], 'recent')
  expect(out.map((x) => x.id)).toEqual(['b', 'a'])
})

test('rank-recent: grouped by posted day, best to worst within each day', () => {
  const out = sortJobs([j('a', 40, 1), j('b', 95, 2), j('c', 80, 1), j('d', 60, 2)], 'rank-recent')
  expect(out.map((x) => x.id)).toEqual(['c', 'a', 'b', 'd'])
})

test('location: alphabetical, unknown last', () => {
  const out = sortJobs([j('a', 50, 0, { location: 'NYC' }), j('b', 50, 0), j('c', 50, 0, { location: 'Austin' })], 'location')
  expect(out.map((x) => x.id)).toEqual(['c', 'a', 'b'])
})

test('does not mutate the input array', () => {
  const input = [j('a', 10, 0), j('b', 90, 0)]
  sortJobs(input, 'rank')
  expect(input.map((x) => x.id)).toEqual(['a', 'b'])
})
