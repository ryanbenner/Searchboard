import { join } from 'node:path'
import { expect, test } from 'vitest'
import { Runner, buildRunArgs } from '../runner'

test('buildRunArgs shape', () => {
  expect(buildRunArgs('/d', false)).toEqual(['run', 'python', '-m', 'searchboard', 'run',
    '--profile', join('/d', 'profile.yml'), '--data-dir', '/d', '--no-email'])
  expect(buildRunArgs('/d', true)).not.toContain('--no-email')
})

test('start streams classified lines from stdout+stderr and reports done', async () => {
  const lines: Array<[string, string]> = []
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const done = new Promise<any>((resolve) => {
    const r = new Runner({ onLine: (l, k) => lines.push([l, k]), onDone: resolve })
    r.start(process.execPath, ['-e', "console.log('raw=5 filtered=3'); console.error('done in 1s')"], process.cwd(), {})
    expect(r.running).toBe(true)
  })
  const rec = await done
  expect(rec.exitCode).toBe(0)
  expect(rec.found).toBe(3)
  expect(lines).toContainEqual(['raw=5 filtered=3', 'dim'])
  expect(lines).toContainEqual(['done in 1s', 'ok'])
})

test('non-zero exit is recorded, not thrown', async () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const done = new Promise<any>((resolve) => {
    new Runner({ onLine: () => {}, onDone: resolve }).start(process.execPath, ['-e', 'process.exit(2)'], process.cwd(), {})
  })
  expect((await done).exitCode).toBe(2)
})
