# JobScraper

Personal daily job-search pipeline. Pulls listings from sustainable APIs
(Greenhouse, Lever, Ashby, RemoteOK, Remotive, We Work Remotely, HN
Who's Hiring), filters them against `profile.yml`, asks Claude Haiku
to rank survivors, and emails me a digest each morning.

**Phase 1 only.** No resume tailoring, no auto-apply (yet).

## How it runs

`.github/workflows/daily.yml` triggers `python -m jobscraper run` at
14:00 UTC daily (7am PT). The job commits `data/seen.sqlite`,
`data/latest.xlsx`, `data/<date>.xlsx`, and any newly-discovered
companies back to the repo.

## First-time setup

### 1. Gmail app password

The pipeline sends mail via your Gmail. You need an **app password**
(not your real Google password):

1. Visit <https://myaccount.google.com/security> → enable 2-Step Verification.
2. Visit <https://myaccount.google.com/apppasswords> → create one named "JobScraper".
3. Copy the 16-character password — you'll use it as `SMTP_PASS`.

### 2. Anthropic API key

<https://console.anthropic.com/settings/keys> → create a key. Copy it.

### 3. Set GitHub Actions secrets

```bash
gh secret set ANTHROPIC_API_KEY -b "sk-ant-..."
gh secret set SMTP_HOST         -b "smtp.gmail.com"
gh secret set SMTP_PORT         -b "587"
gh secret set SMTP_USER         -b "scrubbed@example.com"
gh secret set SMTP_PASS         -b "<gmail app password>"
gh secret set EMAIL_TO          -b "scrubbed@example.com"
```

### 4. Trigger a manual run to verify

```bash
gh workflow run daily
gh run watch
```

Open the latest commit on `main` once it finishes — you should see a
new `data/<date>.xlsx`, and an email in your inbox.

## Local development

```bash
uv sync --extra dev
uv run pytest
```

To run the pipeline locally (uses live network, but you can swap in
fake env vars to skip email):

```bash
ANTHROPIC_API_KEY=... \
SMTP_HOST=smtp.gmail.com SMTP_PORT=587 \
SMTP_USER=... SMTP_PASS=... EMAIL_TO=... \
uv run python -m jobscraper run
```

## Editing your profile

`profile.yml` is the single source of truth for what counts as a "good
match." Edit it any time and the next run picks up the changes.

`companies.yml` grows automatically as new ATS slugs are observed in
other sources. You can hand-edit it (add favorites, remove slugs, push
slugs into `disabled` to mute them).
