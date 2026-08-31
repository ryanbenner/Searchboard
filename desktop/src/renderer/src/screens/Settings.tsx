import React, { useContext, useEffect, useState } from 'react'
import type { SecretStatus, ValidationIssue } from '../../../shared/types'
import { Shell } from '../App'

const SMTP_KEYS = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS', 'EMAIL_TO'] as const

export function Settings(): React.JSX.Element {
  const s = useContext(Shell)
  const [codeRepo, setCodeRepo] = useState('')
  const [dataRepo, setDataRepo] = useState('')
  const [emailOnManualRuns, setEmailOnManualRuns] = useState(false)
  const [secrets, setSecrets] = useState<SecretStatus | null>(null)
  const [draftSecrets, setDraftSecrets] = useState<Record<string, string>>({})
  const [issues, setIssues] = useState<ValidationIssue[]>([])
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    void window.searchboard.settingsGet().then(({ config, secrets, issues }) => {
      setCodeRepo(config.codeRepo)
      setDataRepo(config.dataRepo)
      setEmailOnManualRuns(config.emailOnManualRuns)
      setSecrets(secrets)
      setIssues(issues)
    })
  }, [])

  const save = async (): Promise<void> => {
    setError(null)
    setSaved(false)
    await window.searchboard.settingsSet({ codeRepo, dataRepo, emailOnManualRuns })
    const secretPatch = Object.fromEntries(Object.entries(draftSecrets).filter(([, v]) => v.trim() !== ''))
    if (Object.keys(secretPatch).length) {
      try {
        await window.searchboard.secretsSet(secretPatch)
      } catch (e) {
        setError(String((e as Error).message))
        return
      }
    }
    setDraftSecrets({})
    await s.refreshSettings()
    const { secrets, issues } = await window.searchboard.settingsGet()
    setSecrets(secrets)
    setIssues(issues)
    setSaved(true)
  }

  const secretField = (key: string): React.JSX.Element => {
    const isSet = Boolean(secrets?.[key as keyof SecretStatus])
    const required = key === 'ANTHROPIC_API_KEY' && !isSet
    return (
      <div className="field" key={key}>
        <label>
          {key}
          {required && <span className="required-star">*</span>}
        </label>
        <input
          className={'input' + (required ? ' input-required' : '')}
          type="password"
          placeholder={isSet ? '•••••• (set)' : 'not set'}
          value={draftSecrets[key] ?? ''}
          onChange={(e) => setDraftSecrets((d) => ({ ...d, [key]: e.target.value }))}
        />
      </div>
    )
  }

  return (
    <>
      <header className="screen-header">
        <div>
          <div className="kicker">Configuration</div>
          <h3>Settings</h3>
        </div>
      </header>
      <div className="content">
        <div style={{ maxWidth: 640, display: 'flex', flexDirection: 'column', gap: 22.4 }}>
          <section className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 16.8 }}>
            <div className="card-kicker">Paths &amp; behavior</div>
            <div className="field">
              <label>Code repo path</label>
              <input className="input" value={codeRepo} onChange={(e) => setCodeRepo(e.target.value)} placeholder="/path/to/Searchboard" />
            </div>
            <div className="field">
              <label>Data repo path</label>
              <input className="input" value={dataRepo} onChange={(e) => setDataRepo(e.target.value)} placeholder="/path/to/Searchboard-data" />
            </div>
            <label className="radio">
              <input type="checkbox" checked={emailOnManualRuns} onChange={(e) => setEmailOnManualRuns(e.target.checked)} />
              Send digest email on manual runs
            </label>
          </section>
          <section className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 16.8 }}>
            <div className="card-kicker">Keys</div>
            {secretField('ANTHROPIC_API_KEY')}
            {secretField('ANTHROPIC_WORKSPACE_ID')}
            {emailOnManualRuns && SMTP_KEYS.map(secretField)}
          </section>
          <div style={{ display: 'flex', gap: 11.2, alignItems: 'center' }}>
            <button className="btn btn-primary" onClick={() => void save()}>
              Save
            </button>
            {saved && issues.length === 0 && <span className="text-muted" style={{ fontSize: 13.5 }}>Saved — all checks pass.</span>}
          </div>
          {error && <div className="banner banner-error">{error}</div>}
          {issues
            .filter((i) => i.field !== 'ANTHROPIC_API_KEY')
            .map((i) => (
              <div className="banner banner-error" key={i.field + i.message}>
                {i.message}
              </div>
            ))}
        </div>
      </div>
    </>
  )
}
