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

Edit `league.json`:

- `leagueName`
- `teams`
- each team's:
  - `managerName`
  - `teamName`
  - `url`
  - `roster`

Shared app/source settings stay in `docs/config.js` and normally do not need to change.

`league.json` is the one file you swap to reuse this project for another league.

## Shared app settings

`docs/config.js` now contains only shared settings such as:

- `sourceLabel`
- `sourceUrl`
- `updateCadenceLabel`
- `liveSweatsTimeGateEnabled`
- `scoreFeedUrl`
- `scoreFeedTableId`
- `scoreFeedPlayerColumn`
- `scoreFeedPointsColumn`

## League file shape

```json
{
  "leagueName": "My Fantasy League",
  "teams": [
    {
      "managerName": "Alice",
      "teamName": "River Rats",
      "url": "https://optional-team-link.example",
      "roster": ["Player One", "Player Two"]
    }
  ]
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

The generated `docs/data.json` also carries the league metadata needed by the frontend, so after editing `league.json` you only need to run:

```bash
python3 scripts/update_data.py
```

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
