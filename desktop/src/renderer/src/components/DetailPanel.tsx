import React, { useContext, useEffect, useRef, useState } from 'react'
import { STATUSES } from '../../../shared/types'
import { Shell } from '../App'
import { fmtAgo, fmtSalary } from '../format'

export function DetailPanel(): React.JSX.Element | null {
  const s = useContext(Shell)
  const job = s.jobs.find((j) => j.id === s.selectedId)
  const [notes, setNotes] = useState(job?.notes ?? '')
  const debounce = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    setNotes(job?.notes ?? '')
  }, [job?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => () => {
    if (debounce.current) clearTimeout(debounce.current)
  }, [])

  if (!job) return null

  const setStatus = async (status: (typeof STATUSES)[number]): Promise<void> => {
    await window.searchboard.jobsUpdate(job.id, { status })
    await s.refreshJobs()
  }

  const onNotes = (value: string): void => {
    setNotes(value)
    if (s.running) return
    if (debounce.current) clearTimeout(debounce.current)
    debounce.current = setTimeout(() => {
      void window.searchboard.jobsUpdate(job.id, { notes: value }).then(() => s.refreshJobs())
    }, 600)
  }

  const timeline: Array<[string, string]> = [[`Scraped from ${job.source ?? 'scraped'}`, job.firstSeen]]
  if (job.sentAt) timeline.push(['Emailed in digest', job.sentAt])
  if (job.statusUpdatedAt) timeline.push([`Marked ${job.status}`, job.statusUpdatedAt])

  return (
    <aside className="detail">
      <div style={{ padding: '22.4px 16.8px', display: 'flex', flexDirection: 'column', gap: 16.8 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 11.2 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="kicker">{job.source ?? 'scraped'}</div>
            <h5>{job.title}</h5>
            <div className="text-muted" style={{ fontSize: 14, marginTop: 2.8 }}>
              {job.company}
              {job.location ? ` · ${job.location}` : ''}
            </div>
          </div>
          <button className="btn btn-secondary btn-icon" onClick={() => s.setSelectedId(null)}>
            ×
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8.4 }}>
          <div className="tile">
            <div className="tile-label">Salary</div>
            <div style={{ fontSize: 14.5, marginTop: 2.8 }}>{fmtSalary(job.salaryMin, job.salaryMax)}</div>
          </div>
          <div className="tile">
            <div className="tile-label">Posted</div>
            <div style={{ fontSize: 14.5, marginTop: 2.8 }}>{fmtAgo(job.postedAt ?? job.firstSeen)}</div>
          </div>
          <div className="tile">
            <div className="tile-label">Score</div>
            <div style={{ fontSize: 14.5, marginTop: 2.8 }}>{job.score ?? '—'}</div>
          </div>
          <div className="tile">
            <div className="tile-label">Emailed</div>
            <div style={{ fontSize: 14.5, marginTop: 2.8 }}>{job.sentAt ? fmtAgo(job.sentAt) : 'not yet'}</div>
          </div>
        </div>

        <div>
          <div className="tile-label" style={{ marginBottom: 8.4 }}>
            Status
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5.6 }}>
            {STATUSES.map((st) => (
              <button key={st} className={'chip' + (job.status === st ? ' active' : '')} disabled={s.running} onClick={() => void setStatus(st)}>
                {st}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8.4 }}>
          {timeline.map(([label, when]) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8.4, fontSize: 13.5 }}>
              <span className="dot" />
              <span>{label}</span>
              <span className="text-muted" style={{ marginLeft: 'auto' }}>
                {when}
              </span>
            </div>
          ))}
        </div>

        {job.rationale && (
          <p className="text-muted" style={{ fontSize: 13.5, lineHeight: 1.6 }}>
            {job.rationale}
          </p>
        )}

        <div className="field">
          <label>Notes</label>
          <textarea className="input" value={notes} onChange={(e) => onNotes(e.target.value)} placeholder="Anything worth remembering…" />
        </div>

        <div style={{ display: 'flex', gap: 8.4 }}>
          <button
            className="btn btn-primary"
            style={{ flex: 1 }}
            onClick={() => void window.searchboard.jobsOpenUrl(job.id).then(() => s.refreshJobs())}
          >
            Open posting
          </button>
          <button
            className="btn btn-secondary"
            disabled={s.running}
            onClick={() =>
              void window.searchboard.jobsUpdate(job.id, { status: 'Dismissed' }).then(() => {
                s.setSelectedId(null)
                void s.refreshJobs()
              })
            }
          >
            Dismiss
          </button>
        </div>
      </div>
    </aside>
  )
}
