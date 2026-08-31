import Database from 'better-sqlite3'
import { appliedFor, type Status } from './statusRules'

export const MIN_SCORE = 45

export interface JobRow {
  id: string
  company: string
  title: string
  url: string
  firstSeen: string
  lastSeen: string
  sentAt: string | null
  score: number | null
  status: Status
  statusUpdatedAt: string | null
  notes: string
  source: string | null
  location: string | null
  salaryMin: number | null
  salaryMax: number | null
  postedAt: string | null
  rationale: string | null
}

export class Db {
  private c: Database.Database

  constructor(sqlitePath: string) {
    this.c = new Database(sqlitePath, { timeout: 5000 })
    for (const [name, typ] of [['status', 'TEXT'], ['status_updated_at', 'TEXT']]) {
      try {
        this.c.exec(`ALTER TABLE seen ADD COLUMN ${name} ${typ}`)
      } catch {
        /* exists */
      }
    }
  }

  // untouched postings age out after 2 weeks or below MIN_SCORE; anything the
  // user acted on stays. low scores stay stored so the pipeline never re-ranks them
  listJobs(): JobRow[] {
    return this.c
      .prepare(`SELECT * FROM seen
        WHERE (status IS NULL OR status != 'Dismissed')
          AND (applied = 1 OR (
            COALESCE(posted_at, first_seen) >= date('now', '-14 days')
            AND (ranked_score IS NULL OR ranked_score >= ${MIN_SCORE})))
        ORDER BY first_seen DESC, id`)
      .all()
      .map(rowToJob)
  }

  updateJob(id: string, patch: { status?: Status; notes?: string }): void {
    if (patch.status !== undefined) {
      this.c
        .prepare(`UPDATE seen SET status=?, status_updated_at=?, applied=? WHERE id=?`)
        .run(patch.status, new Date().toISOString().slice(0, 10), appliedFor(patch.status), id)
    }
    if (patch.notes !== undefined) {
      this.c.prepare(`UPDATE seen SET notes=? WHERE id=?`).run(patch.notes, id)
    }
  }

  counts(): Record<string, number> {
    const out: Record<string, number> = { Total: 0 }
    for (const j of this.listJobs()) {
      out.Total++
      out[j.status] = (out[j.status] ?? 0) + 1
    }
    return out
  }

  close(): void {
    this.c.close()
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function rowToJob(r: any): JobRow {
  return {
    id: r.id,
    company: r.company,
    title: r.title,
    url: r.url,
    firstSeen: r.first_seen,
    lastSeen: r.last_seen,
    sentAt: r.sent_at,
    score: r.ranked_score,
    status: (r.status ?? 'New') as Status,
    statusUpdatedAt: r.status_updated_at,
    notes: r.notes ?? '',
    source: r.source,
    location: r.location,
    salaryMin: r.salary_min,
    salaryMax: r.salary_max,
    postedAt: r.posted_at,
    rationale: r.rationale,
  }
}
