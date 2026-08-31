import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { parseEnv, serializeEnv } from './envfile'
import { which } from './paths'

const SECRET_KEYS = ['ANTHROPIC_API_KEY', 'SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS', 'EMAIL_TO'] as const

export interface AppConfig {
  codeRepo: string
  dataRepo: string
  emailOnManualRuns: boolean
}
export interface SecretStatus {
  ANTHROPIC_API_KEY: boolean
  SMTP_HOST: boolean
  SMTP_PORT: boolean
  SMTP_USER: boolean
  SMTP_PASS: boolean
  EMAIL_TO: boolean
}
export interface ValidationIssue {
  field: string
  message: string
}

export class Settings {
  constructor(private configPath: string) {}

  get(): AppConfig {
    const defaults: AppConfig = { codeRepo: '', dataRepo: '', emailOnManualRuns: false }
    if (!existsSync(this.configPath)) return defaults
    try {
      return { ...defaults, ...JSON.parse(readFileSync(this.configPath, 'utf8')) }
    } catch {
      return defaults
    }
  }

  set(patch: Partial<AppConfig>): void {
    mkdirSync(dirname(this.configPath), { recursive: true })
    writeFileSync(this.configPath, JSON.stringify({ ...this.get(), ...patch }, null, 2) + '\n')
  }

  private envPath(): string {
    return join(this.get().codeRepo, '.env')
  }

  readSecrets(): Record<string, string> {
    const p = this.envPath()
    if (!existsSync(p)) return {}
    const all = parseEnv(readFileSync(p, 'utf8'))
    const out: Record<string, string> = {}
    for (const k of SECRET_KEYS) if (k in all) out[k] = all[k]
    return out
  }

  secretStatus(): SecretStatus {
    const secrets = this.readSecrets()
    const out = {} as Record<(typeof SECRET_KEYS)[number], boolean>
    for (const k of SECRET_KEYS) out[k] = Boolean(secrets[k])
    return out
  }

  setSecrets(patch: Record<string, string>): void {
    const ignorePath = join(this.get().codeRepo, '.gitignore')
    const ignored =
      existsSync(ignorePath) &&
      readFileSync(ignorePath, 'utf8')
        .split(/\r?\n/)
        .some((l) => l.trim() === '.env')
    if (!ignored) throw new Error('.env is not gitignored in the code repo — refusing to write secrets')
    const p = this.envPath()
    const existing = existsSync(p) ? readFileSync(p, 'utf8') : ''
    writeFileSync(p, serializeEnv(existing, patch))
  }

  validate(): ValidationIssue[] {
    const issues: ValidationIssue[] = []
    const { codeRepo, dataRepo } = this.get()
    if (!codeRepo || !existsSync(codeRepo)) {
      issues.push({ field: 'codeRepo', message: `code repo not found at "${codeRepo}"` })
    } else if (!existsSync(join(codeRepo, 'pyproject.toml'))) {
      issues.push({ field: 'codeRepo', message: `no pyproject.toml in "${codeRepo}" — is this the Searchboard code repo?` })
    }
    if (!dataRepo || !existsSync(dataRepo)) {
      issues.push({ field: 'dataRepo', message: `data repo not found at "${dataRepo}"` })
    } else {
      if (!existsSync(join(dataRepo, 'seen.sqlite')))
        issues.push({ field: 'dataRepo', message: `no seen.sqlite in "${dataRepo}"` })
      if (!existsSync(join(dataRepo, 'profile.yml')))
        issues.push({ field: 'dataRepo', message: `no profile.yml in "${dataRepo}"` })
    }
    if (!which('git')) issues.push({ field: 'git', message: 'git not found on PATH' })
    if (!which('uv')) issues.push({ field: 'uv', message: 'uv not found on PATH' })
    if (!this.secretStatus().ANTHROPIC_API_KEY)
      issues.push({ field: 'ANTHROPIC_API_KEY', message: `ANTHROPIC_API_KEY not set in ${this.envPath()}` })
    return issues
  }
}
