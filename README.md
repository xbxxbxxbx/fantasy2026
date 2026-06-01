# Poker Fantasy Leaderboard

Static GitHub Pages leaderboard for a poker fantasy draft.

## What it does

- Fetches Poker.org team pages with Python
- Writes a static `docs/data.json` snapshot
- Totals each fantasy manager's latest team score
- Ranks managers on a clean leaderboard page

## Configure it

The current config is set up for Poker.org team pages.

Edit `docs/config.js`:

- `leagueName` and `leagueDescription`
- `teamSources`: each manager name, team name, and team URL
- `teamPageTableSelector`: table selector on the team pages
- `teamPagePlayerColumn` and `teamPagePointsColumn`

### Team source shape

Each team entry supports:

```js
{
  managerName: "Trampstamp",
  teamName: "lowerbackstamp",
  url: "https://www.poker.org/fantasy/wsop/2026/team/lowerbackstamp/",
}
```

The parser expects a table with columns like `PLAYER` and `SCORE`, which matches the sample you pasted.

## Update the data

Run:

```bash
python3 scripts/update_data.py
```

That fetches each configured team page and rewrites `docs/data.json`.

## Automated refresh

The repo includes a GitHub Actions workflow at `.github/workflows/update-leaderboard.yml`.

- Manual run: trigger `Update leaderboard data` from the Actions tab
- Scheduled run: every 30 minutes

For scheduled updates to work, the repo must be on GitHub with Actions enabled.

## Publish to GitHub Pages

1. Push this repo to GitHub.
2. In the repo settings, open `Pages`.
3. Set the deploy source to `Deploy from a branch`.
4. Choose your main branch and the `/docs` folder.
5. Save.

## Local preview

Serve the repo root or the `docs` folder with a small static server, then open the page in a browser.
