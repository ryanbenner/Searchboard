import type { JobRow } from '../../shared/types'

export type SortMode = 'rank-recent' | 'rank' | 'recent' | 'location'

export const SORT_LABELS: Record<SortMode, string> = {
  'rank-recent': 'Ranked + recent',
  rank: 'Top ranked',
  recent: 'Newest',
  location: 'Location',
}

const ageDays = (iso: string): number =>
  Math.max(0, Math.floor((Date.now() - new Date(iso + 'T00:00:00Z').getTime()) / 864e5))

// score fades by 2 points per day of age, so fresh decent matches beat stale great ones
const blend = (j: JobRow): number => (j.score ?? 0) - 2 * ageDays(j.firstSeen)

type Cmp = (a: JobRow, b: JobRow) => number
const byScore: Cmp = (a, b) => (b.score ?? -1) - (a.score ?? -1)
const byRecent: Cmp = (a, b) => b.firstSeen.localeCompare(a.firstSeen)

const COMPARATORS: Record<SortMode, Cmp> = {
  rank: (a, b) => byScore(a, b) || byRecent(a, b),
  recent: (a, b) => byRecent(a, b) || byScore(a, b),
  'rank-recent': (a, b) => blend(b) - blend(a) || byRecent(a, b),
  location: (a, b) => {
    if (a.location == null && b.location == null) return byScore(a, b)
    if (a.location == null) return 1
    if (b.location == null) return -1
    return a.location.localeCompare(b.location) || byScore(a, b)
  },
}

export function sortJobs(jobs: JobRow[], mode: SortMode): JobRow[] {
  return [...jobs].sort(COMPARATORS[mode])
}
