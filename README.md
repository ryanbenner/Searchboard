# Searchboard

Personal job-search pipeline plus a desktop app to work the results.

The pipeline pulls listings from sustainable APIs (Greenhouse, Lever,
Ashby, SmartRecruiters, RemoteOK, Remotive, We Work Remotely, HN Who's
Hiring), filters them against your `profile.yml`, asks Claude Haiku to
score the survivors 0–100, and emails a digest of fresh matches. The
desktop app (Electron, `desktop/`) browses and tracks those jobs, edits
your search criteria, and runs the pipeline on demand with live logs.

No resume tailoring, no auto-apply.

## How it runs

`.github/workflows/daily.yml` runs `python -m searchboard run` at 14:00
UTC (7am PT) on **weekdays**. Each run:

- Clones a **separate private** data repo and restores `profile.yml` +
  cumulative `seen.sqlite` from it.
- Scrapes listings, filters, verifies URLs, and ranks them.
- Emails the digest: up to 15 jobs scoring ≥ 50, **posted within the
  last 5 days**, still live today, and never emailed before. Each job is
  emailed at most once, ever. No eligible jobs → no email.
- Writes `latest.xlsx` (New today / Still open / All ranked; the latter
  two cover postings from the last 14 days) and a dated snapshot.
- Pushes `seen.sqlite` + snapshots back to the private data repo, and any
  newly discovered ATS company slugs back to this repo.

### Ranking cost

Only jobs without a stored score are sent to the API; everything else
reuses its score from `seen.sqlite`. A change to `profile.yml` (detected
by content hash) triggers one full re-rank, after which skipping resumes.
Every run prints `rank_cost=$… (input_tokens=… output_tokens=…)` and
`scored_new=N reused=M` to stderr. Steady state is a few new jobs a day
(fractions of a cent); a full re-rank of ~550 jobs is about $0.55.

### CLI flags

```
python -m searchboard run [--no-email] [--profile PATH] [--data-dir PATH]
```

Defaults (`profile.yml`, `data/`, email on) are what the workflow uses.
`--no-email` skips the digest and does not mark jobs as sent — the
desktop app uses this for manual runs.

## Desktop app

`desktop/` is an Electron + React app (macOS arm64 dmg, Windows nsis).
It needs `git`, `uv`, and local clones of this repo and the data repo;
point it at both in Settings and paste your `ANTHROPIC_API_KEY` (stored
in this repo's gitignored `.env`).

- **Overview** — tracked / new / applied counts, reply rate, pipeline
  funnel, latest arrivals.
- **All jobs** — score column, search, status chips, and sorting
  (Newest + ranked, Newest, Top ranked, Location). Shows untouched
  postings from the last **2 weeks** with score ≥ 45; anything you've
  acted on stays regardless. Detail panel: status picker (New → Visited
  → Applied → Heard back → Interviewing → Offer / Rejected / Ghosted),
  notes, timeline, Dismiss, Open posting.
- **Search** — edits `profile.yml` in the data repo (titles, exclusions,
  locations, remote-only, minimum salary); Save & run kicks the pipeline.
- **Runs** — run history and a live, colorized log pane.
- Status/notes edits and profile changes auto-commit and push to the data
  repo after a 15s debounce; the app pulls on launch and before runs.

See `desktop/README.md` for dev and build commands.

## First-time setup

### 1. Create a private data repo

Create an empty private repo (suggested name: `<your-username>/Searchboard-data`).
This will hold your `profile.yml`, daily xlsx snapshots, and the cumulative
`seen.sqlite` log. Nothing here is published.

### 2. Generate a fine-grained PAT

At <https://github.com/settings/personal-access-tokens/new>:

- **Resource owner:** your account
- **Repository access:** Only select repositories → your `Searchboard-data`
- **Permissions:** Contents → Read and write

Copy the generated token.

### 3. Gmail app password

The pipeline sends mail via your Gmail. You need an **app password**
(not your real Google password):

1. Visit <https://myaccount.google.com/security> → enable 2-Step Verification.
2. Visit <https://myaccount.google.com/apppasswords> → create one named "Searchboard".
3. Copy the 16-character password — you'll use it as `SMTP_PASS`.

### 4. Anthropic API key

<https://console.anthropic.com/settings/keys> → create a key. Copy it —
the Console shows it only once. Keep a local copy in `.env` (the desktop
app's Settings screen writes it there for you).

### 5. Set GitHub Actions secrets

```bash
gh secret set ANTHROPIC_API_KEY   # paste at the prompt
gh secret set ANTHROPIC_WORKSPACE_ID  # wrkspc_... id; required for identity-linked keys
gh secret set DATA_REPO_TOKEN     # fine-grained PAT from step 2
gh secret set SMTP_HOST -b "smtp.gmail.com"
gh secret set SMTP_PORT -b "587"
gh secret set SMTP_USER -b "<your-gmail-address>"
gh secret set SMTP_PASS           # gmail app password
gh secret set EMAIL_TO  -b "<your-gmail-address>"
```

### 6. Seed the data repo

Copy `profile.example.yml` to `profile.yml`, fill it out, then push to
your private data repo:

```bash
cp profile.example.yml profile.yml
# edit profile.yml with your details
cd /tmp && git clone https://github.com/<you>/Searchboard-data.git
cp <repo-path>/profile.yml /tmp/Searchboard-data/
cd /tmp/Searchboard-data
git add profile.yml
git commit -m "seed profile"
git push
```

### 7. Update the workflow with your data-repo URL

In `.github/workflows/daily.yml`, set `DATA_REPO` to your data repo path.

### 8. Trigger a manual run to verify

```bash
gh workflow run daily
gh run watch
```

When it finishes you should have an email in your inbox and new
contents in your `Searchboard-data` private repo.

## Local development

```bash
uv sync --extra dev
uv run pytest
```

To run the pipeline locally without emailing:

```bash
ANTHROPIC_API_KEY=... uv run python -m searchboard run --no-email \
  --profile ../Searchboard-data/profile.yml --data-dir ../Searchboard-data
```

Desktop app: `cd desktop && npm install && npm run dev` (tests: `npm test`).

## Editing your profile

`profile.yml` is the single source of truth for what counts as a "good
match." Edit it in the desktop app's Search screen or directly in the
private data repo. The workflow always restores from the private data
repo at run time, so changes there are authoritative.

`companies.yml` grows automatically as new ATS slugs are observed in
other sources. It's tracked in this public repo (it's just a list of
company slugs — nothing personal).
