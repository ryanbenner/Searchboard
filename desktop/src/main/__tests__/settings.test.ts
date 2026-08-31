import { expect, test } from 'vitest'
import { mkdtempSync, writeFileSync, mkdirSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { Settings } from '../settings'

function fakeRepos() {
  const root = mkdtempSync(join(tmpdir(), 'sb-'))
  const code = join(root, 'code')
  const data = join(root, 'data')
  mkdirSync(code)
  mkdirSync(data)
  writeFileSync(join(code, 'pyproject.toml'), '')
  writeFileSync(join(code, '.gitignore'), '.env\n')
  writeFileSync(join(data, 'seen.sqlite'), '')
  writeFileSync(join(data, 'profile.yml'), 'name: x\n')
  return { root, code, data }
}

test('get/set round-trips config.json', () => {
  const { root, code, data } = fakeRepos()
  const s = new Settings(join(root, 'config.json'))
  s.set({ codeRepo: code, dataRepo: data, emailOnManualRuns: false })
  const s2 = new Settings(join(root, 'config.json'))
  expect(s2.get().codeRepo).toBe(code)
})

test('setSecrets writes .env in code repo; status reflects it; values stay out of status', () => {
  const { root, code, data } = fakeRepos()
  const s = new Settings(join(root, 'config.json'))
  s.set({ codeRepo: code, dataRepo: data, emailOnManualRuns: false })
  s.setSecrets({ ANTHROPIC_API_KEY: 'sk-test' })
  expect(readFileSync(join(code, '.env'), 'utf8')).toContain('ANTHROPIC_API_KEY=sk-test')
  expect(s.secretStatus().ANTHROPIC_API_KEY).toBe(true)
  expect(s.secretStatus().SMTP_HOST).toBe(false)
  expect(JSON.stringify(s.secretStatus())).not.toContain('sk-test')
})

test('setSecrets refuses when .env is not gitignored', () => {
  const { root, code, data } = fakeRepos()
  writeFileSync(join(code, '.gitignore'), 'nothing\n')
  const s = new Settings(join(root, 'config.json'))
  s.set({ codeRepo: code, dataRepo: data, emailOnManualRuns: false })
  expect(() => s.setSecrets({ ANTHROPIC_API_KEY: 'x' })).toThrow(/gitignore/)
})

test('validate reports each missing prerequisite by field', () => {
  const { root, code } = fakeRepos()
  const s = new Settings(join(root, 'config.json'))
  s.set({ codeRepo: code, dataRepo: join(root, 'nope'), emailOnManualRuns: false })
  const fields = s.validate().map((i) => i.field)
  expect(fields).toContain('dataRepo')
  expect(fields).toContain('ANTHROPIC_API_KEY')
})
