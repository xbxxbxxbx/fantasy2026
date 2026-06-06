# Poker Fantasy Leaderboard

Static GitHub Pages leaderboard for a WSOP fantasy draft.

## Current architecture

- Frontend: static HTML, CSS, and browser JS under `docs/`
- Refresh script: `scripts/update_data.py`
- Generated artifacts:
  - `docs/data.json`
  - `docs/active-players.json`
  - `docs/history/*.json`
  - `docs/25k-player-history.json`
  - `docs/latest-changes.json`

## Data sources

- Primary score feed: `https://www.25kfantasy.com/players/`
- Active-sweat feed: `https://www.25kfantasy.com/sweat`

## Make your own league

You do not need to understand the codebase to reuse this project.

The simplest workflow is:

1. Collect the league information
2. Give that information to an LLM using the prompt below
3. Have it update `league.json`
4. Run `python3 scripts/update_data.py`

### Collect this information

For each league, collect:

- The league name
- Each manager name
- Each team name
- Each team link, if you have one
- Each team's full player list

### Prompt for an LLM

Copy this prompt and replace the placeholders with your real league data:

```text
Update the file `league.json` for this repo.

Rules:
- Keep valid JSON
- Do not change any files except `league.json`
- Preserve the existing structure of the file
- Replace the old league data with the new league data below
- For each team, fill in:
  - `managerName`
  - `teamName`
  - `url`
  - `roster`
- Keep roster player names exactly as written

New league data:

League name:
<LEAGUE NAME>

Teams:
1. Manager: <MANAGER 1>
   Team name: <TEAM NAME 1>
   URL: <TEAM URL 1 or leave blank>
   Roster:
   - <PLAYER 1>
   - <PLAYER 2>
   - <PLAYER 3>

2. Manager: <MANAGER 2>
   Team name: <TEAM NAME 2>
   URL: <TEAM URL 2 or leave blank>
   Roster:
   - <PLAYER 1>
   - <PLAYER 2>
   - <PLAYER 3>

Continue until all teams are included.
```

### Build the new snapshot

After `league.json` is updated, run:

```bash
python3 scripts/update_data.py
```

That regenerates the site data for the new league.

### What you usually do not need to change

Most of the time, leave these alone:

- `docs/config.json`
- `docs/index.html`
- `docs/styles.css`
- `docs/js/*`

For reuse, `league.json` is the main file you swap.

## Technical config

`docs/config.json` contains shared settings such as:

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
- `docs/latest-changes.json` when you add a manual product update entry

The generated `docs/data.json` also carries the league metadata needed by the frontend, so after editing `league.json` you only need to run:

```bash
python3 scripts/update_data.py
```

## Automated refresh

Workflow:

- `.github/workflows/update-leaderboard.yml`

Current schedule:

- Every 10 minutes at `:03, :13, :23, :33, :43, :53`

The workflow commits generated data back to `master`.

## Daily points semantics

The displayed `+points` are not based on midnight ET.

They reset at:

- `10:00 AM ET`

This means:

- Overnight Vegas updates before 10 AM ET still count toward the previous poker day
- The first successful scrape after 10 AM ET becomes the new baseline
- Later updates keep accumulating from that baseline

The UI label for this is:

- `since restart`

## GitHub Pages

Use:

- Branch: `master`
- Folder: `/docs`

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
- latest-changes modal update rules
