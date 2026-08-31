import React, { useContext, useEffect, useRef, useState } from 'react'
import type { LineKind, RunRecord } from '../../../shared/types'
import { classifyLine } from '../../../shared/types'
import { Shell } from '../App'
import { fmtDuration } from '../format'

export function Runs(): React.JSX.Element {
  const s = useContext(Shell)
  const [history, setHistory] = useState<RunRecord[]>([])
  const [selected, setSelected] = useState<RunRecord | null>(null)
  const [live, setLive] = useState<Array<[string, string, LineKind]>>([])
  const wasRunning = useRef(s.running)
  const pane = useRef<HTMLDivElement>(null)

  useEffect(() => {
    void window.searchboard.runsHistory().then((h) => {
      setHistory(h)
      setSelected((cur) => cur ?? h[0] ?? null)
    })
  }, [s.lastRun])

  useEffect(() => {
    if (s.running && !wasRunning.current) setLive([])
    wasRunning.current = s.running
  }, [s.running])

  useEffect(() => {
    const off = window.searchboard.onRunLine((line, kind) => {
      const t = new Date().toTimeString().slice(0, 8)
      setLive((prev) => [...prev, [t, line, kind]])
    })
    return off
  }, [])

  useEffect(() => {
    if (pane.current) pane.current.scrollTop = pane.current.scrollHeight
  }, [live])

  const stored = selected?.log ? selected.log.split('\n') : []

  return (
    <>
      <header className="screen-header">
        <div>
          <div className="kicker">Activity</div>
          <h3>Runs &amp; output</h3>
          <p className="text-muted" style={{ fontSize: 13, marginTop: 5.6 }}>
            Manual runs from this machine; the 7:00 daily workflow runs on GitHub.
          </p>
        </div>
      </header>
      <div className="content">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16.8, alignItems: 'start' }}>
          <section className="panel">
            <div className="card-kicker" style={{ marginBottom: 11.2 }}>
              Run history
            </div>
            <table className="table">
              <thead>
                <tr>
                  <th>Started</th>
                  <th>Found</th>
                  <th>New</th>
                  <th>Duration</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {history.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => setSelected(r)}
                    style={{ cursor: 'pointer', boxShadow: selected?.id === r.id ? 'inset 2px 0 0 var(--color-accent)' : undefined }}
                  >
                    <td>{new Date(r.startedAt).toLocaleString()}</td>
                    <td>{r.found ?? '—'}</td>
                    <td>{r.added ?? '—'}</td>
                    <td>{fmtDuration(r.durationMs)}</td>
                    <td>{r.exitCode === 0 ? <span className="tag tag-accent">ok</span> : <span className="tag log-error">failed</span>}</td>
                  </tr>
                ))}
                {history.length === 0 && (
                  <tr>
                    <td colSpan={5} className="text-muted">
                      No runs recorded yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
          <section>
            <div className="card-kicker" style={{ marginBottom: 11.2 }}>
              Output log
            </div>
            <div className="log-pane" ref={pane}>
              {s.running || live.length > 0
                ? live.map(([t, line, kind], i) => (
                    <div className="log-row" key={i}>
                      <span className="log-t">{t}</span>
                      <span className={'log-' + kind}>{line}</span>
                    </div>
                  ))
                : stored.map((line, i) => (
                    <div className="log-row" key={i}>
                      <span className="log-t">+{i}</span>
                      <span className={'log-' + classifyLine(line)}>{line}</span>
                    </div>
                  ))}
              {!s.running && live.length === 0 && stored.length === 0 && <span className="log-dim">No output yet — press Run scraper.</span>}
            </div>
          </section>
        </div>
      </div>
    </>
  )
}
