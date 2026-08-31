import Database from 'better-sqlite3'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { expect, test } from 'vitest'
import { Db } from '../db'

function seed(rows: Array<Partial<Record<string, unknown>> & { id: string }>): string {
  const p = join(mkdtempSync(join(tmpdir(), 'sbdb-')), 'seen.sqlite')
  const c = new Database(p)
  c.exec(`CREATE TABLE seen (
    id TEXT PRIMARY KEY, company TEXT, title TEXT, url TEXT,
    first_seen DATE NOT NULL, last_seen DATE NOT NULL, ranked_score INTEGER,
    applied INTEGER NOT NULL DEFAULT 0, notes TEXT, sent_at DATE,
    source TEXT, location TEXT, salary_min INTEGER, salary_max INTEGER,
    posted_at DATE, rationale TEXT)`)
  const ins = c.prepare(`INSERT INTO seen (id, company, title, url, first_seen, last_seen, ranked_score)
    VALUES (@id, @company, @title, @url, @first_seen, @last_seen, @score)`)
  const today = new Date().toISOString().slice(0, 10)
  for (const r of rows)
    ins.run({ company: 'C', title: 'T', url: 'u', first_seen: today, last_seen: today, score: 70, ...r })
  c.close()
  return p
}

test('migration adds status columns to a db without them; NULL reads as New', () => {
  const db = new Db(seed([{ id: 'a:b:1' }]))
  expect(db.listJobs()[0].status).toBe('New')
})

test('updateJob writes status, timestamps it, syncs applied', () => {
  const p = seed([{ id: 'a:b:1' }])
  const db = new Db(p)
  db.updateJob('a:b:1', { status: 'Interviewing' })
  const row = new Database(p).prepare('SELECT status, applied, status_updated_at FROM seen').get() as any
  expect(row.status).toBe('Interviewing')
  expect(row.applied).toBe(1)
  expect(row.status_updated_at).toMatch(/^\d{4}-\d{2}-\d{2}/)
})

test('Dismissed rows vanish from listJobs and counts, but stay in the table', () => {
  const p = seed([{ id: 'a:b:1' }, { id: 'a:b:2' }])
  const db = new Db(p)
  db.updateJob('a:b:1', { status: 'Dismissed' })
  expect(db.listJobs().map((j) => j.id)).toEqual(['a:b:2'])
  expect(db.counts().Total).toBe(1)
  expect(new Database(p).prepare('SELECT COUNT(*) n FROM seen').get()).toMatchObject({ n: 2 })
})

test('notes update leaves status untouched', () => {
  const p = seed([{ id: 'a:b:1' }])
  const db = new Db(p)
  db.updateJob('a:b:1', { notes: 'call back friday' })
  const j = db.listJobs()[0]
  expect(j.notes).toBe('call back friday')
  expect(j.status).toBe('New')
})

test('untouched jobs older than 3 weeks age out; acted-on jobs stay', () => {
  const day = (n: number): string => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10)
  const p = seed([
    { id: 'old:untouched', first_seen: day(30) },
    { id: 'old:applied', first_seen: day(30) },
    { id: 'old:seen:fresh:post', first_seen: day(30) },
    { id: 'fresh', first_seen: day(2) },
  ])
  const c = new Database(p)
  c.prepare(`UPDATE seen SET posted_at=? WHERE id='old:seen:fresh:post'`).run(day(3))
  c.close()
  const db = new Db(p)
  db.updateJob('old:applied', { status: 'Applied' })
  expect(db.listJobs().map((j) => j.id).sort()).toEqual(['fresh', 'old:applied', 'old:seen:fresh:post'])
  expect(db.counts().Total).toBe(3)
})
