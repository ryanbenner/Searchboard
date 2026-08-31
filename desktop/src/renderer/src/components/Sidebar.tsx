import React, { useContext } from 'react'
import { Shell } from '../App'

const NAV = [
  ['overview', 'Overview'],
  ['jobs', 'All jobs'],
  ['search', 'Search'],
  ['runs', 'Runs'],
] as const

export function Sidebar(): React.JSX.Element {
  const s = useContext(Shell)
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">S</span>Searchboard
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2.8 }}>
        {NAV.map(([key, label]) => (
          <button
            key={key}
            className={'nav-item' + (s.screen === key ? ' active' : '')}
            disabled={!s.settingsOk}
            onClick={() => s.setScreen(key)}
          >
            <span className="nav-mark" />
            {label}
            <span className="nav-badge">{key === 'jobs' ? s.jobs.length || '' : key === 'runs' && s.running ? '●' : ''}</span>
          </button>
        ))}
      </nav>
      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 8.4 }}>
        {(s.syncState === 'conflict' || s.syncState === 'offline') && (
          <div className="banner banner-error">
            sync: {s.syncState}
            {s.syncDetail ? ` — ${s.syncDetail.slice(0, 120)}` : ''}
          </div>
        )}
        <div className="run-card">
          <div
            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, letterSpacing: '.08em', textTransform: 'uppercase' }}
            className="text-muted"
          >
            <span className={'run-dot' + (s.running ? ' running' : '')} />
            {s.running ? 'Running' : 'Idle'}
          </div>
          <div className="text-muted" style={{ fontSize: 12 }}>
            {s.running ? 'pipeline · in progress' : s.lastRun ? `last run ${new Date(s.lastRun.startedAt).toLocaleString()}` : 'no runs yet'}
          </div>
          <button className="btn btn-primary btn-block" disabled={s.running || !s.settingsOk} onClick={() => void s.startRun()}>
            Run scraper
          </button>
        </div>
        <button className={'nav-item' + (s.screen === 'settings' ? ' active' : '')} onClick={() => s.setScreen('settings')}>
          <span className="nav-mark" />
          Settings
        </button>
      </div>
    </aside>
  )
}
