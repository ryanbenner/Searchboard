import React, { useContext, useEffect, useState } from 'react'
import type { SearchProfile } from '../../../shared/types'
import { Shell } from '../App'

const SOURCES = ['Greenhouse', 'Lever', 'Ashby', 'SmartRecruiters', 'RemoteOK', 'Remotive', 'WeWorkRemotely', "HN Who's Hiring"]

export function Search(): React.JSX.Element {
  const s = useContext(Shell)
  const [p, setP] = useState<SearchProfile | null>(null)
  const [titleDraft, setTitleDraft] = useState('')
  const [locationDraft, setLocationDraft] = useState('')
  const [excludeText, setExcludeText] = useState('')
  const [salaryText, setSalaryText] = useState('')

  useEffect(() => {
    void window.searchboard.profileGet().then((prof) => {
      setP(prof)
      setExcludeText(prof.excludeKeywords.join(', '))
      setSalaryText(String(prof.minSalary || ''))
    })
  }, [])

  if (!p) return <></>

  const assemble = (): SearchProfile => ({
    ...p,
    excludeKeywords: excludeText.split(',').map((x) => x.trim()).filter(Boolean),
    minSalary: parseInt(salaryText.replace(/[^0-9]/g, ''), 10) || 0,
  })

  const save = async (): Promise<void> => {
    await window.searchboard.profileSet(assemble())
  }

  const addChip = (key: 'titles' | 'locations', draft: string, clear: () => void): void => {
    const v = draft.trim()
    if (!v || p[key].includes(v)) return
    setP({ ...p, [key]: [...p[key], v] })
    clear()
  }

  const chipRow = (key: 'titles' | 'locations', tagClass: string, draft: string, setDraft: (v: string) => void, placeholder: string): React.JSX.Element => (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 5.6 }}>
      {p[key].map((label) => (
        <span className={`tag ${tagClass}`} key={label}>
          {label}
          <button
            style={{ all: 'unset', cursor: 'pointer', opacity: 0.7 }}
            onClick={() => setP({ ...p, [key]: p[key].filter((t) => t !== label) })}
          >
            ×
          </button>
        </span>
      ))}
      <input
        className="input"
        style={{ width: 180 }}
        placeholder={placeholder}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') addChip(key, draft, () => setDraft(''))
        }}
      />
    </div>
  )

  return (
    <>
      <header className="screen-header">
        <div>
          <div className="kicker">Configuration</div>
          <h3>Search criteria</h3>
          <p className="text-muted" style={{ fontSize: 14, marginTop: 5.6 }}>
            Saved to profile.yml in the data repo — the daily workflow reads the same file.
          </p>
        </div>
      </header>
      <div className="content">
        <div style={{ maxWidth: 640, display: 'flex', flexDirection: 'column', gap: 22.4 }}>
          <section className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 16.8 }}>
            <div className="card-kicker">Titles &amp; keywords</div>
            {chipRow('titles', 'tag-outline', titleDraft, setTitleDraft, 'Add a title…')}
            <div className="field">
              <label>Exclude anything matching</label>
              <input className="input" value={excludeText} onChange={(e) => setExcludeText(e.target.value)} placeholder="clearance, contract, …" />
            </div>
          </section>
          <section className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 16.8 }}>
            <div className="card-kicker">Locations</div>
            {chipRow('locations', 'tag-neutral', locationDraft, setLocationDraft, 'Add a metro…')}
            <label className="radio">
              <input type="checkbox" checked={p.remoteOnly} onChange={(e) => setP({ ...p, remoteOnly: e.target.checked })} />
              Remote-friendly only
            </label>
          </section>
          <section className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 16.8 }}>
            <div className="card-kicker">Minimum salary</div>
            <div className="field">
              <label>USD per year</label>
              <input className="input" style={{ width: 180 }} value={salaryText} onChange={(e) => setSalaryText(e.target.value)} placeholder="120000" />
            </div>
          </section>
          <section className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 11.2 }}>
            <div className="card-kicker">Sources</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5.6 }}>
              {SOURCES.map((src) => (
                <span className="tag tag-neutral" key={src}>
                  {src}
                </span>
              ))}
            </div>
            <span className="text-muted" style={{ fontSize: 13 }}>
              All sources run every time; toggles may come later.
            </span>
          </section>
          <div style={{ display: 'flex', gap: 8.4 }}>
            <button className="btn btn-secondary" onClick={() => void save()}>
              Save
            </button>
            <button
              className="btn btn-primary"
              disabled={s.running}
              onClick={() => void save().then(() => s.startRun())}
            >
              Save &amp; run
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
