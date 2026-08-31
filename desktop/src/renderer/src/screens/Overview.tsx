import React, { useContext, useMemo } from 'react'
import { STATUSES } from '../../../shared/types'
import { Shell } from '../App'
import { fmtAgo } from '../format'

const APPLIED_SET = ['Applied', 'Heard back', 'Interviewing', 'Offer', 'Rejected', 'Ghosted']
const ANSWERED_SET = ['Heard back', 'Interviewing', 'Offer', 'Rejected']
const NEUTRAL_BARS = new Set(['Visited', 'Rejected', 'Ghosted'])

export function Overview(): React.JSX.Element {
  const s = useContext(Shell)

  const counts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const j of s.jobs) c[j.status] = (c[j.status] ?? 0) + 1
    return c
  }, [s.jobs])

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const applied = APPLIED_SET.reduce((n, st) => n + (counts[st] ?? 0), 0)
  const answered = ANSWERED_SET.reduce((n, st) => n + (counts[st] ?? 0), 0)
  const maxCount = Math.max(1, ...STATUSES.map((st) => counts[st] ?? 0))
  const latest = s.jobs.slice(0, 6)

  const stat = (label: string, value: React.ReactNode, note?: string): React.JSX.Element => (
    <div className="card elev-sm stat-card" key={label}>
      <div className="card-kicker">{label}</div>
      <div className="stat-value">{value}</div>
      {note && (
        <div className="text-muted" style={{ fontSize: 13 }}>
          {note}
        </div>
      )}
    </div>
  )

  return (
    <>
      <header className="screen-header">
        <div>
          <div className="kicker">Overview</div>
          <h3>{greeting}</h3>
          <p className="text-muted" style={{ fontSize: 14, marginTop: 5.6 }}>
            {s.lastRun ? `Last run found ${s.lastRun.added ?? '?'} new roles.` : 'No runs recorded on this machine yet.'}
          </p>
        </div>
      </header>
      <div className="content">
        <div style={{ maxWidth: 1080, display: 'flex', flexDirection: 'column', gap: 22.4 }}>
          <div className="stat-grid">
            {stat('Tracked', s.jobs.length)}
            {stat('New', counts['New'] ?? 0)}
            {stat('Applied', applied)}
            {stat('Reply rate', applied ? `${Math.round((100 * answered) / applied)}%` : '—', `${answered} of ${applied} answered`)}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1.35fr 1fr', gap: 16.8 }}>
            <section className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 11.2 }}>
              <div className="card-kicker">Pipeline</div>
              {STATUSES.map((st) => (
                <div className="funnel-row" key={st}>
                  <span style={{ fontSize: 13.5 }}>{st}</span>
                  <span className="funnel-track">
                    <span
                      className="funnel-bar"
                      style={{
                        width: `${Math.max(3, (100 * (counts[st] ?? 0)) / maxCount)}%`,
                        background: NEUTRAL_BARS.has(st) ? 'var(--color-neutral-700)' : undefined,
                      }}
                    />
                  </span>
                  <span style={{ fontSize: 13, fontVariantNumeric: 'tabular-nums', textAlign: 'right' }}>{counts[st] ?? 0}</span>
                </div>
              ))}
            </section>
            <section className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 8.4 }}>
              <div className="card-kicker">Latest</div>
              {latest.map((j) => (
                <button
                  key={j.id}
                  style={{ all: 'unset', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 11.2, padding: '5.6px 0' }}
                  onClick={() => {
                    s.setSelectedId(j.id)
                    s.setScreen('jobs')
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14.5, fontFamily: 'var(--font-heading)', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {j.title}
                    </div>
                    <div className="text-muted" style={{ fontSize: 13 }}>
                      {j.company}
                      {j.location ? ` · ${j.location}` : ''}
                    </div>
                  </div>
                  <span className="text-muted" style={{ fontSize: 12.5, flex: 'none' }}>
                    {fmtAgo(j.firstSeen)}
                  </span>
                </button>
              ))}
              {latest.length === 0 && (
                <span className="text-muted" style={{ fontSize: 13.5 }}>
                  Nothing scraped yet.
                </span>
              )}
            </section>
          </div>
        </div>
      </div>
    </>
  )
}
