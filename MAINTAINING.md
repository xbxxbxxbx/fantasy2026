# Maintainer Runbook

## Live deployment assumptions

- default branch: `master`
- GitHub Pages source: `master /docs`
- workflow file: `.github/workflows/update-leaderboard.yml`
- workflow cadence: every 10 minutes

## Rollback handles

- rollback branch: `rollback/pre-streamline`
- rollback tag: `pre-streamline-live`

If the live site breaks after a cleanup merge, use one of these:

1. revert the merge commit on `master`
2. reset Pages back to the rollback branch or rollback tag state

This cleanup is intended to remain merge-revertable one phase at a time.

## Local preview

Run a local server from the repo root:

```bash
python3 -m http.server 4181 --directory docs
```

Open:

- `http://localhost:4181`

Do not use `file://.../docs/index.html`. The page fetches JSON assets and needs HTTP.

## Published artifacts

Generated on the scheduled workflow and committed to the repo:

- `docs/data.json`
- `docs/active-players.json`
- `docs/history/YYYY-MM-DD.json`
- `docs/25k-player-history.json`

Hand-maintained source files:

- `league.json`
- `docs/config.js`
- `docs/index.html`
- `docs/styles.css`
- `docs/js/*.js`
- `docs/app.js`
- `scripts/update_data.py`
- `scripts/update_data_lib/*.py`

## Data sources

- score feed: `https://www.25kfantasy.com/players/`
- active sweats:
  - page: `https://www.25kfantasy.com/sweat`
  - POST endpoint: `https://www.25kfantasy.com/process/sweat`

## Daily delta semantics

`pointsChange` in `docs/data.json` means:

- points gained since the first successful scrape after the 10 AM ET poker-day reset

It does **not** mean:

- since the last workflow run
- since midnight ET
- since the source site itself updated

The reset rule is:

- before 10:00 AM ET, new points still belong to the prior poker day
- at or after 10:00 AM ET, the first successful scrape becomes the new baseline

`pointsChangeSincePrevious` still exists in the snapshot for previous-run comparison, but the UI uses the daily baseline value.

## League setup

For a new league, only edit:

- `league.json`

Then run:

```bash
python3 scripts/update_data.py
```

The scraper reads:

- `league.json` for league/team/roster data
- `docs/config.js` for shared source and feature settings

The frontend reads:

- `docs/data.json`
- `docs/active-players.json`
- `docs/25k-player-history.json`

## Validation before merging

Frontend:

```bash
node --check docs/app.js
```

Python:

```bash
python3 -m py_compile scripts/update_data.py scripts/update_data_lib/*.py
python3 scripts/update_data.py
```

Then refresh the local preview and verify:

- live sweats gate before/after 6 PM EST
- leaderboard renders
- roster jump links work
- historical widget opens
- daily deltas still render

## Latest changes modal

Before pushing a meaningful UI or product change:

1. add a new entry at the top of `docs/latest-changes.json`
2. keep the title as `Latest changes`
3. keep summaries short and simple
4. use at most 3 bullet points per entry
5. do not mention minor spacing or implementation details unless they matter to users
6. do not end summary lines with periods

Each entry should include:

- `commit`
- `url`
- `publishedAt`
- `summary`

This file is a running list. Do not trim it to the last 3 changes. The modal is scrollable and will show the full history.

## Verifying the next scheduled run

After merging to `master`:

1. check the latest workflow run in GitHub Actions
2. confirm a new commit landed touching:
   - `docs/data.json`
   - `docs/active-players.json`
   - optionally `docs/history/*.json`
3. confirm the live page `Updated ...` timestamp advances

## Cache busting

Asset version query strings in `docs/index.html` are manual.

When frontend assets change:

- update the shared `?v=...` query string on the CSS and JS tags
- commit that bump with the asset changes

This keeps GitHub Pages clients from holding stale browser assets after deploys.
