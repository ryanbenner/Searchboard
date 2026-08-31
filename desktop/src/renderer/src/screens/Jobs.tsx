import React, { useContext, useMemo, useState } from 'react'
import { STATUSES } from '../../../shared/types'
import { Shell } from '../App'
import { DetailPanel } from '../components/DetailPanel'
import { fmtAgo, fmtSalary } from '../format'
import { SORT_LABELS, sortJobs, type SortMode } from '../sortJobs'

const slug = (status: string): string => status.toLowerCase().replace(' ', '-')

export function Jobs(): React.JSX.Element {
  const s = useContext(Shell)
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<string>('All')
  const [sort, setSort] = useState<SortMode>('rank-recent')

  const counts = useMemo(() => {
    const c: Record<string, number> = { All: s.jobs.length }
    for (const j of s.jobs) c[j.status] = (c[j.status] ?? 0) + 1
    return c
  }, [s.jobs])

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    const filtered = s.jobs.filter(
      (j) =>
        (filter === 'All' || j.status === filter) &&
        (!q || `${j.title} ${j.company} ${j.location ?? ''}`.toLowerCase().includes(q))
    )
    return sortJobs(filtered, sort)
  }, [s.jobs, query, filter, sort])

  return (
    <>
      <header className="screen-header">
        <div>
          <div className="kicker">History</div>
          <h3>All jobs</h3>
        </div>
      </header>
      <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>
        <div className="content">
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8.4, marginBottom: 16.8 }}>
            <input className="input" style={{ width: 260 }} placeholder="Filter by title, company, location…" value={query} onChange={(e) => setQuery(e.target.value)} />
            <select className="input" value={sort} onChange={(e) => setSort(e.target.value as SortMode)}>
              {(Object.keys(SORT_LABELS) as SortMode[]).map((m) => (
                <option key={m} value={m}>
                  {SORT_LABELS[m]}
                </option>
              ))}
            </select>
            {['All', ...STATUSES].map((st) => (
              <button key={st} className={'chip' + (filter === st ? ' active' : '')} onClick={() => setFilter(st)}>
                {st}
                <span className="chip-count">{counts[st] ?? 0}</span>
              </button>
            ))}
            <span className="text-muted" style={{ marginLeft: 'auto', fontSize: 13 }}>
              {visible.length} of {s.jobs.length} shown
            </span>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: 18 }} />
                <th style={{ width: 48 }}>Score</th>
                <th>Role</th>
                <th>Company</th>
                <th>Location</th>
                <th>Salary</th>
                <th>Posted</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((j) => (
                <tr
                  key={j.id}
                  onClick={() => s.setSelectedId(j.id)}
                  style={{ cursor: 'pointer', boxShadow: s.selectedId === j.id ? 'inset 2px 0 0 var(--color-accent)' : undefined }}
                >
                  <td>{j.status === 'New' && <span className="dot" />}</td>
                  <td
                    style={{
                      fontFamily: 'var(--font-heading)',
                      fontWeight: 500,
                      fontVariantNumeric: 'tabular-nums',
                      color: j.score == null ? 'var(--color-neutral-600)' : j.score >= 80 ? 'var(--color-accent)' : j.score >= 50 ? 'var(--color-text)' : 'var(--color-neutral-500)',
                    }}
                  >
                    {j.score ?? '—'}
                  </td>
                  <td style={{ fontFamily: 'var(--font-heading)', fontWeight: 500, color: j.status === 'New' ? 'var(--color-text)' : 'color-mix(in srgb, var(--color-text) 72%, transparent)' }}>
                    {j.title}
                  </td>
                  <td>{j.company}</td>
                  <td>{j.location ?? '—'}</td>
                  <td>{fmtSalary(j.salaryMin, j.salaryMax)}</td>
                  <td>{fmtAgo(j.postedAt ?? j.firstSeen)}</td>
                  <td>
                    <span className={'tag tag-status-' + slug(j.status)}>{j.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {s.selectedId && <DetailPanel />}
      </div>
    </>
  )
}
