# Poker Fantasy Leaderboard

A static leaderboard site for a Poker.org fantasy league.

You give the project a list of Poker.org team URLs. It imports the teams, builds the roster data, updates scores, and serves a leaderboard you can preview locally or publish with GitHub Pages.

## Requirements

- A GitHub account
- A copy of this repository
- Python 3.12 or newer
- A settings file named `league.ini`
- Codex, Terminal, or another way to run a few commands
- Codex download page: [chatgpt.com/codex](https://chatgpt.com/codex/)

You do not need to edit code to make your own league.

## 1. Setup

### Quick Start With Codex

This is the shortest setup path. It is 7 steps from cloned code to a live GitHub Pages site with automatic refreshes.

1. Open Codex.
   Download it from [chatgpt.com/codex](https://chatgpt.com/codex/) if you do not have it yet.
2. Ask Codex to clone or open this repository.
3. Open `league.ini`.
4. Set your league name and paste one Poker.org team URL per line under `[Poker.org URLs]`.
5. Ask Codex to run:

```bash
python3 scripts/update_data.py
```

6. Push the updated files to GitHub, then turn on GitHub Pages with:
   - Branch: `master`
   - Folder: `/docs`
7. Set up cron-job.org so GitHub runs the update workflow automatically.

After GitHub Pages finishes publishing and cron-job.org is set up, your league site is live and auto-refreshing.

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

Blank lines are ignored. Lines starting with `#` are ignored.

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

## Technical Reference

For data sources, refresh behavior, cron-job.org setup, generated files, and manual league-data details, see [TECHNICAL-REFERENCE.md](/Users/trstowell/Documents/fantasy/TECHNICAL-REFERENCE.md). Use that file when you are wiring up refresh automation or need the project internals.

## Maintainers

See [MAINTAINING.md](/Users/trstowell/Documents/fantasy/MAINTAINING.md) for rollback instructions, artifact contracts, deploy checks, cache-busting policy, and latest-changes modal rules.
