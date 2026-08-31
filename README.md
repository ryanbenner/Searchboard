# Searchboard

Daily job-search pipeline. Pulls listings from sustainable APIs
(Greenhouse, Lever, Ashby, RemoteOK, Remotive, We Work Remotely, HN
Who's Hiring), filters them against your `profile.yml`, asks Claude Haiku
to rank survivors, and emails the operator a daily digest of new matches.

**Phase 1 / 1.5.** No resume tailoring, no auto-apply (yet).

## How it runs

`.github/workflows/daily.yml` triggers `python -m searchboard run` at
14:00 UTC daily (7am PT). Each run:

- Clones a **separate private** data repo and restores `profile.yml` +
  cumulative `seen.sqlite` from it.
- Scrapes listings, filters, verifies URLs, ranks the survivors, and
  picks the top 15 jobs that haven't been emailed before and are still
  alive today.
- Sends the digest (if non-empty).
- Pushes the updated `seen.sqlite` and per-day xlsx snapshot back to
  the private data repo.
- Pushes any newly discovered ATS company slugs back to this (public)
  repo.

All personal data — profile, run history, snapshots — lives in the
private data repo. This public repo contains code and seed config only.

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

<https://console.anthropic.com/settings/keys> → create a key. Copy it.

### 5. Set GitHub Actions secrets

```bash
gh secret set ANTHROPIC_API_KEY -b "sk-ant-..."
gh secret set DATA_REPO_TOKEN   -b "<fine-grained PAT from step 2>"
gh secret set SMTP_HOST         -b "smtp.gmail.com"
gh secret set SMTP_PORT         -b "587"
gh secret set SMTP_USER         -b "<your-gmail-address>"
gh secret set SMTP_PASS         -b "<gmail app password>"
gh secret set EMAIL_TO          -b "<your-gmail-address>"
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

In `.github/workflows/daily.yml`, replace `<owner>/Searchboard-data`
with your data repo path.

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

To run the pipeline locally:

```bash
# Make sure profile.yml exists locally (it's gitignored).
ANTHROPIC_API_KEY=... \
SMTP_HOST=smtp.gmail.com SMTP_PORT=587 \
SMTP_USER=... SMTP_PASS=... EMAIL_TO=... \
uv run python -m searchboard run
```

## Editing your profile

`profile.yml` is the single source of truth for what counts as a "good
match." Edit it locally OR in the private data repo. The workflow always
restores from the private data repo at run time, so changes there are
authoritative.

`companies.yml` grows automatically as new ATS slugs are observed in
other sources. It's tracked in this public repo (it's just a list of
company slugs — nothing personal).
