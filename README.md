# Poker Fantasy Leaderboard

Static GitHub Pages leaderboard for a WSOP fantasy draft.

## Current architecture

- frontend: static HTML, CSS, and browser JS under `docs/`
- primary score feed: `https://www.25kfantasy.com/players/`
- active-sweat feed: `https://www.25kfantasy.com/sweat`
- refresh script: `scripts/update_data.py`
- generated artifacts:
  - `docs/data.json`
  - `docs/active-players.json`
  - `docs/history/*.json`
  - `docs/25k-player-history.json`

## Configure it

Edit `docs/config.js`:

- `leagueName`
- `sourceLabel`
- `sourceUrl`
- `updateCadenceLabel`
- `scoreFeedUrl`
- `scoreFeedTableId`
- `scoreFeedPlayerColumn`
- `scoreFeedPointsColumn`
- `teamSources`

Each roster entry uses this shape:

```js
{
  managerName: "Trampstamp",
  teamName: "lowerbackstamp",
  url: "https://www.poker.org/fantasy/wsop/2026/team/lowerbackstamp/",
  roster: ["Player One", "Player Two"],
}
```

## Update the published data

Run:

```bash
python3 scripts/update_data.py
```

That updates:

- `docs/data.json`
- `docs/active-players.json`
- `docs/history/YYYY-MM-DD.json` when needed

## Automated refresh

Workflow:

- `.github/workflows/update-leaderboard.yml`

Current schedule:

- every 10 minutes

The workflow commits generated data back to `master`.

## GitHub Pages

Use:

- branch: `master`
- folder: `/docs`

## Local preview

Run:

```bash
python3 -m http.server 4181 --directory docs
```

Then open:

- `http://localhost:4181`

Do not use `file://.../docs/index.html`.

## Maintenance

See `MAINTAINING.md` for:

- rollback instructions
- artifact contracts
- delta semantics
- deploy verification
- cache-busting policy
