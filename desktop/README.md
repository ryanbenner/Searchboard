# Searchboard desktop

Electron app for browsing/tracking scraped jobs, editing `profile.yml`, and running the pipeline locally.

## Prerequisites (per machine)

- `git` on PATH
- `uv` on PATH
- A clone of this repo (the code repo) and a clone of `Searchboard-data` with push access

On first launch, open Settings, point the app at both clones, and paste your `ANTHROPIC_API_KEY` (stored in the code repo's gitignored `.env`).

## Development

```bash
npm install
npm run dev
```

Tests: `npm test`. Typecheck: `npm run typecheck`.

## Build

macOS (arm64 dmg, run on a Mac):

```bash
npm run build:mac    # → dist/searchboard-<version>.dmg
```

Windows (nsis installer — must be run on a Windows machine; better-sqlite3 is rebuilt for Electron there):

```bash
npm run build:win
```
