import { expect, test } from 'vitest'
import { parseEnv, serializeEnv } from '../envfile'

test('parses KEY=value, ignores comments/blanks, strips quotes', () => {
  expect(parseEnv('# c\n\nA=1\nB="two"\nC=th ree\n')).toEqual({ A: '1', B: 'two', C: 'th ree' })
})
test('serialize preserves unrelated lines and comments', () => {
  const out = serializeEnv('# keep\nOTHER=x\nA=old\n', { A: 'new', B: '2' })
  expect(out).toBe('# keep\nOTHER=x\nA=new\nB=2\n')
})
test('serialize from empty file', () => {
  expect(serializeEnv('', { A: '1' })).toBe('A=1\n')
})
