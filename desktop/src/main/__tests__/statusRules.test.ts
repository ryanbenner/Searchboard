import { expect, test } from 'vitest'
import { appliedFor } from '../statusRules'

test('post-application statuses set applied', () => {
  for (const s of ['Applied', 'Heard back', 'Interviewing', 'Offer', 'Rejected', 'Ghosted'] as const)
    expect(appliedFor(s)).toBe(1)
})
test('pre-application statuses clear applied', () => {
  for (const s of ['New', 'Visited', 'Dismissed'] as const) expect(appliedFor(s)).toBe(0)
})
