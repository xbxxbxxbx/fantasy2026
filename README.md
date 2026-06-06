# Poker Fantasy Leaderboard

A static leaderboard site for a Poker.org fantasy league.

You give the project a list of Poker.org team URLs. It imports the teams, builds the roster data, updates scores, and serves a leaderboard you can preview locally or publish with GitHub Pages.

## Requirements

- A GitHub account
- A copy of this repository
- Python 3.12 or newer
- A settings file named `league.ini`
- Codex, Terminal, or another way to run a few commands

You do not need to edit code to make your own league.

## 1. Setup

### Quick Start With Codex

Use this if you are not comfortable with command-line setup.

1. Open Codex.
2. Ask Codex to clone or open this repository.
3. Open `league.ini`.
4. Set your league name and paste one Poker.org team URL per line under `[Poker.org URLs]`.
5. Ask Codex:

```text
Update my league data from league.ini and start a local preview.
```

Codex should run:

```bash
python3 scripts/update_data.py
python3 -m http.server 4181 --directory docs
```

Then open:

- `http://localhost:4181`

Do not open `docs/index.html` directly with `file://`. The site loads JSON files and needs a local web server.

### Settings File

Edit `league.ini` in the project root.

Example:

```ini
[League]
name = My Poker Fantasy League

[Poker.org URLs]
https://www.poker.org/fantasy/wsop/2026/team/example-team/
https://www.poker.org/fantasy/wsop/2026/team/another-team/
```

Blank lines are ignored. Lines starting with `#` are ignored. Do not put `-` before the URLs.

### Update League Data

Run:

```bash
python3 scripts/update_data.py
```

This is the only normal data command. It reads `league.ini`, refreshes `league.json` when the settings changed, updates scores, and writes the public site data in `docs/`.

### Preview The Site

Run:

```bash
python3 -m http.server 4181 --directory docs
```

Open:

- `http://localhost:4181`

If another app is already using port `4181`, use another port:

```bash
python3 -m http.server 4182 --directory docs
```

Then open:

- `http://localhost:4182`

### Publish With GitHub Pages

In GitHub Pages settings, use:

- Branch: `master`
- Folder: `/docs`

After you push changes to GitHub, GitHub Pages serves the files from `docs/`.

## 2. Where The Data Comes From

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

## 3. How Data Is Refreshed

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

The included GitHub Actions workflow updates the leaderboard data on a schedule and commits the generated files back to `master`.

Current schedule:

- Every 10 minutes at `:03, :13, :23, :33, :43, :53`

If you do not want automatic updates, disable the workflow in GitHub Actions.

The automatic refresh updates scores and Live Sweats. It also rebuilds `league.json` when `league.ini` changes and creates `docs/25k-player-history.json` if the historical file is missing.

### Optional: Use cron-job.org

GitHub Actions already has a built-in schedule. That is the easiest option.

Use cron-job.org only if you want an outside service to trigger updates for you.

What cron-job.org does:

- wakes up on your schedule
- sends an HTTP request to GitHub
- GitHub runs the update workflow
- the workflow updates generated data and commits it back to `master`

#### 1. Create a GitHub token

In GitHub, create a personal access token that can trigger Actions for this repository.

For a fine-grained token, give it:

- Repository access: this repository
- Actions permission: read and write

Do not put this token in your repository. It only belongs in cron-job.org.

#### 2. Create a cron-job.org job

In cron-job.org, create a new cron job.

Use these settings:

- URL: `https://api.github.com/repos/OWNER/REPO/actions/workflows/update-leaderboard.yml/dispatches`
- Request method: `POST`
- Schedule: whatever update cadence you want

Replace:

- `OWNER` with your GitHub username or organization
- `REPO` with your repository name

For this repository, the URL would be:

```text
https://api.github.com/repos/xbxxbxxbx/fantasy2026/actions/workflows/update-leaderboard.yml/dispatches
```

#### 3. Add request headers

Add these headers in cron-job.org:

```text
Accept: application/vnd.github+json
Authorization: Bearer YOUR_GITHUB_TOKEN
Content-Type: application/json
```

Replace `YOUR_GITHUB_TOKEN` with the token you created.

#### 4. Add request body

Use this request body:

```json
{
  "ref": "master"
}
```

#### 5. Test it

Run the cron-job.org job once manually.

Then check GitHub:

1. Open your repository.
2. Go to the Actions tab.
3. Open `Update leaderboard data`.
4. Confirm a new run started.
5. Confirm it committed updated data if scores changed.

If the job fails, check:

- the token has Actions read/write permission
- the URL uses the correct owner and repo
- the workflow file name is `update-leaderboard.yml`
- the request method is `POST`
- the body is valid JSON

## What Files Matter

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

## Daily Points

The displayed `+points` reset at:

- `10:00 AM ET`

Overnight Las Vegas results before 10 AM ET still count toward the previous poker day.

## Manual League Data

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

## Maintainers

See `MAINTAINING.md` for rollback instructions, artifact contracts, deploy checks, cache-busting policy, and latest-changes modal rules.
