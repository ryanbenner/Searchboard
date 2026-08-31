export const STATUSES = ['New', 'Visited', 'Applied', 'Heard back', 'Interviewing', 'Offer', 'Rejected', 'Ghosted'] as const
export type Status = (typeof STATUSES)[number] | 'Dismissed'
const APPLIED = new Set<Status>(['Applied', 'Heard back', 'Interviewing', 'Offer', 'Rejected', 'Ghosted'])
export const appliedFor = (status: Status): 0 | 1 => (APPLIED.has(status) ? 1 : 0)
