import type { JobRow } from '../../shared/types'

export type SortMode = 'rank-recent' | 'recent' | 'rank' | 'location'

export const SORT_LABELS: Record<SortMode, string> = {
  'rank-recent': 'Newest + ranked',
  recent: 'Newest',
  rank: 'Top ranked',
  location: 'Location',
}

// "posted" is what the job board says; fall back to when we first scraped it
const posted = (j: JobRow): string => j.postedAt ?? j.firstSeen

type Cmp = (a: JobRow, b: JobRow) => number
const byScore: Cmp = (a, b) => (b.score ?? -1) - (a.score ?? -1)
const byPosted: Cmp = (a, b) => posted(b).localeCompare(posted(a))
const byFirstSeen: Cmp = (a, b) => b.firstSeen.localeCompare(a.firstSeen)
const byTitle: Cmp = (a, b) => a.title.localeCompare(b.title)

const COMPARATORS: Record<SortMode, Cmp> = {
  'rank-recent': (a, b) => byPosted(a, b) || byScore(a, b),
  recent: (a, b) => byPosted(a, b) || byFirstSeen(a, b) || byTitle(a, b),
  rank: (a, b) => byScore(a, b) || byPosted(a, b),
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
