import { expect, test } from 'vitest'
import { fmtAgo, fmtDuration, fmtErrorDetail, fmtSalary } from '../format'

test('fmtSalary', () => {
  expect(fmtSalary(135000, 160000)).toBe('$135–160k')
  expect(fmtSalary(140000, null)).toBe('$140k+')
  expect(fmtSalary(null, 160000)).toBe('up to $160k')
  expect(fmtSalary(null, null)).toBe('—')
})
test('fmtAgo', () => {
  const d = (days: number) => new Date(Date.now() - days * 864e5).toISOString().slice(0, 10)
  expect(fmtAgo(d(0))).toBe('today')
  expect(fmtAgo(d(3))).toBe('3d')
  expect(fmtAgo(null)).toBe('—')
})
test('fmtDuration', () => {
  expect(fmtDuration(33000)).toBe('33s')
  expect(fmtDuration(130000)).toBe('2m 10s')
})

test('fmtErrorDetail strips git prefixes, keeps first line, caps length', () => {
  expect(fmtErrorDetail("error: cannot lock ref 'x': boom\nmore detail\n")).toBe("cannot lock ref 'x': boom")
  expect(fmtErrorDetail('fatal: ' + 'a'.repeat(200))).toBe('a'.repeat(100) + '…')
  expect(fmtErrorDetail('\n\nfirst real line')).toBe('first real line')
  expect(fmtErrorDetail(undefined)).toBe('')
})
