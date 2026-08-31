import { execFileSync } from 'node:child_process'
import { mkdtempSync, writeFileSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { expect, test } from 'vitest'
import { Sync } from '../sync'

const git = (cwd: string, ...args: string[]) => execFileSync('git', args, { cwd }).toString()

function setup() {
  const root = mkdtempSync(join(tmpdir(), 'sbg-'))
  const origin = join(root, 'origin.git')
  execFileSync('git', ['init', '--bare', '--initial-branch=main', origin])
  const a = join(root, 'a')
  execFileSync('git', ['clone', origin, a])
  git(a, 'config', 'user.email', 't@t')
  git(a, 'config', 'user.name', 't')
  git(a, 'checkout', '-B', 'main')
  writeFileSync(join(a, 'seen.sqlite'), 'v1')
  git(a, 'add', '-A')
  git(a, 'commit', '-m', 'init')
  git(a, 'push', '-u', 'origin', 'main')
  return { origin, a, root }
}

test('commitAndPush pushes local changes; a fresh clone sees them', async () => {
  const { origin, a, root } = setup()
  const s = new Sync(a, () => {})
  writeFileSync(join(a, 'seen.sqlite'), 'v2')
  expect(await s.commitAndPush('searchboard test')).toBe('idle')
  const b = join(root, 'b')
  execFileSync('git', ['clone', origin, b])
  expect(readFileSync(join(b, 'seen.sqlite'), 'utf8')).toBe('v2')
})

test('commitAndPush with nothing changed is a clean no-op', async () => {
  const { a } = setup()
  const s = new Sync(a, () => {})
  expect(await s.commitAndPush('noop')).toBe('idle')
})

test('rejected push auto-rebases and retries once', async () => {
  const { origin, a, root } = setup()
  const b = join(root, 'b')
  execFileSync('git', ['clone', origin, b])
  git(b, 'config', 'user.email', 't@t')
  git(b, 'config', 'user.name', 't')
  writeFileSync(join(b, 'other.txt'), 'x')
  git(b, 'add', '-A')
  git(b, 'commit', '-m', 'remote change')
  git(b, 'push')
  const s = new Sync(a, () => {})
  writeFileSync(join(a, 'mine.txt'), 'y')
  expect(await s.commitAndPush('mine')).toBe('idle')
  expect(git(a, 'log', '--oneline').split('\n').filter(Boolean).length).toBeGreaterThanOrEqual(3)
})

test('concurrent operations serialize instead of racing git', async () => {
  const { a } = setup()
  const states: string[] = []
  const s = new Sync(a, (st) => states.push(st))
  writeFileSync(join(a, 'seen.sqlite'), 'v2')
  const [r1, r2] = await Promise.all([s.pull(), s.commitAndPush('m')])
  expect(r1).toBe('idle')
  expect(r2).toBe('idle')
  // ops must not interleave: every 'syncing' is resolved before the next begins
  expect(states).toEqual(['syncing', 'idle', 'syncing', 'idle'])
})
