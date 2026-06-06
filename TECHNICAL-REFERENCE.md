# Technical Reference

Use this file for the project details behind the league site: data sources, refresh behavior, generated files, and manual data formats.

## 1. Where The Data Comes From

The public website does not scrape Poker.org or 25KFantasy in a visitor's browser. It reads generated files in `docs/`. The Python scripts create those files.

| What you see or use | Comes from | Stored in |
| --- | --- | --- |
| League title | `[League] name` in `league.ini` | `league.json`, then `docs/data.json` |
| Team names | Poker.org team pages listed in `league.ini` | `league.json`, then `docs/data.json` |
| Team links | Poker.org team URLs from `league.ini` | `league.json`, then `docs/data.json` |
| Manager names | Poker.org owner/manager text when available, otherwise the team name | `league.json`, then `docs/data.json` |
| Rosters | Poker.org roster table on each team page | `league.json` |
| Player scores | 25KFantasy score table configured in `docs/config.json` | `docs/data.json` |
| Team standings | Calculated from rosters plus player scores | `docs/data.json` |
| Daily `+points` | Calculated from today's baseline versus current totals | `docs/data.json` and `docs/history/YYYY-MM-DD.json` |
| Live Sweats | 25KFantasy active-player feed | `docs/active-players.json` |
| Historical-points popup | Older 25KFantasy yearly player pages, fetched during setup if missing | `docs/25k-player-history.json` |
| Site/source labels | `docs/config.json` during setup | `docs/config.js` and `docs/data.json` |
| Latest-changes modal | Maintainer-written release notes | `docs/latest-changes.json` |

### Source Timing

Setup/static sources:

- Poker.org team pages: fetched only when `league.ini` changes or `league.json` is missing.
- Older 25KFantasy yearly pages: fetched only when `docs/25k-player-history.json` is missing.

Live sources:

- Current 25KFantasy scores: fetched every refresh.
- Current 25KFantasy Live Sweats: fetched every refresh.

Local-only files:

- `docs/config.json`: edited in the repo, not fetched by the browser. Setup hard-codes its public values into `docs/config.js`.
- `docs/latest-changes.json`: edited in the repo and read locally by the browser when the latest-changes modal opens. It is not scraped from an external source.

### Data You Edit

- `league.ini`: one settings file with your league name and Poker.org team URLs.

### Generated League Cache

- `league.json`: generated roster data built from `league.ini` and Poker.org team pages.

Most owners should not edit `league.json`. If `league.ini` changes, `scripts/update_data.py` refreshes the cache automatically.

### Data Imported From Poker.org

`scripts/update_data.py` reads each Poker.org team URL from `[Poker.org URLs]` in `league.ini` when `league.json` is missing or stale.

It imports:

- team name
- team page URL
- roster/player names
- manager or owner name when the page exposes one

It writes that information to `league.json`.

Most score refreshes reuse `league.json` instead of reloading every Poker.org team page. If someone entered the wrong URL or needs to add/remove a team, update `league.ini`, run `python3 scripts/update_data.py`, and push the updated `league.ini`, `league.json`, and generated `docs/` files.

### Data Read From 25KFantasy

`docs/config.json` controls the score source.

Current score source:

- Label: `25KFantasy`
- URL: `https://www.25kfantasy.com/players/`
- Player column: `Player`
- Points column: `Score`

`scripts/update_data.py` reads that table, matches each rostered player by name, calculates team totals, and writes the leaderboard snapshot to `docs/data.json`.

Live Sweats data comes from 25KFantasy too. The script reads the current active-player feed and writes `docs/active-players.json`. The site uses that file to show live players and live sweat indicators.

### Data Calculated By This Project

- Team standings: calculated from `league.json` rosters plus 25KFantasy player scores.
- Per-player points: copied from the 25KFantasy score table when the player name matches.
- Daily `+points`: calculated by comparing current team totals to the day's baseline snapshot.
- Daily baseline files: stored in `docs/history/YYYY-MM-DD.json`.
- Last updated time: stored in `docs/data.json` when the refresh script runs.

Daily `+points` reset at 10:00 AM ET. Overnight Las Vegas results before 10:00 AM ET still count toward the previous poker day.

### Setup-Time Historical Data

`docs/25k-player-history.json` is used by the historical-points popup.

If that file is missing, `scripts/update_data.py` fetches older 25KFantasy yearly player pages and creates it. Once it exists, normal score refreshes do not fetch historical years again.

### Data Maintained Separately

- `docs/latest-changes.json`: plain-English release notes shown in the latest-changes modal. This is maintained by whoever updates the project.
- `docs/config.json`: score source settings and display settings used by setup/update scripts.

## 2. How Data Is Refreshed

### Manual Refresh

To refresh scores yourself, run:

```bash
python3 scripts/update_data.py
```

In plain English, that command:

1. opens `league.ini`
2. refreshes `league.json` only if the settings changed or the cache is missing
3. creates `docs/25k-player-history.json` only if the historical file is missing
4. downloads the current 25KFantasy score table
5. matches player names from your rosters to the score table
6. totals each team
7. refreshes the Live Sweats file
8. writes the new public JSON files in `docs/`

The website then reads the newest files from `docs/`.

If you are previewing locally, refresh the browser after the command finishes. If the site is published on GitHub Pages, push the updated files to GitHub.

### Automatic Refresh With GitHub Actions

The included GitHub Actions workflow updates the leaderboard data and commits the generated files back to `master`.

Current schedule:

- Every 10 minutes at `:03, :13, :23, :33, :43, :53`

The automatic refresh updates scores and Live Sweats. It also rebuilds `league.json` when `league.ini` changes and creates `docs/25k-player-history.json` if the historical file is missing.

## 3. What Files Matter

Most league owners only need to edit:

- `league.ini`: your league name and Poker.org team URLs

Generated files you may see but usually should not edit:

- `league.json`: generated league/roster file
- `docs/data.json`: generated leaderboard data

Most league owners should not need to edit:

- `docs/index.html`
- `docs/styles.css`
- `docs/js/*`
- `scripts/*`

## 4. Daily Points

The displayed `+points` reset at:

- `10:00 AM ET`

Overnight Las Vegas results before 10 AM ET still count toward the previous poker day.

## 5. Manual League Data

If you already have roster data, you can edit `league.json` directly.

Minimal shape:

```json
{
  "teams": [
    {
      "teamName": "Team Name",
      "url": "https://www.poker.org/fantasy/wsop/2026/team/team-name/",
      "roster": ["Player One", "Player Two"]
    }
  ]
}
```

`managerName` is optional. If it is missing, the project uses `teamName`.

## 6. Maintainers

See `MAINTAINING.md` for rollback instructions, artifact contracts, deploy checks, cache-busting policy, and latest-changes modal rules.
