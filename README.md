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

## Quick Start

Quick Start is the automated setup workflow.

Use this if you want Codex to validate your setup file, run the data import, stop on setup errors, and tell you exactly what to fix.

1. Open Codex.
   Download it from [chatgpt.com/codex](https://chatgpt.com/codex/) if you do not have it yet.
2. Ask Codex to clone or open this repository.
3. Open `league.ini`.
4. Set your league name and paste one Poker.org team URL per line under `[Poker.org URLs]`.
5. Ask Codex to follow `QUICKSTART.md`.

The automated workflow will:

- validate `league.ini`
- run setup
- write debug details to `setup.log`
- stop and wait if something needs to be fixed

After Quick Start finishes, continue to:

- `Publish With GitHub Pages`
- `Set Up Automatic Refreshes With cron-job.org`

Those later steps are still manual. The GitHub token and cron-job.org setup are required after either Quick Start or Manual Setup.

## Manual Setup

Use this if you do not want to use the automated workflow.

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

After Manual Setup finishes, continue to:

- `Publish With GitHub Pages`
- `Set Up Automatic Refreshes With cron-job.org`

Those later steps are still manual. The GitHub token and cron-job.org setup are required after either Quick Start or Manual Setup.

## Publish With GitHub Pages

In GitHub Pages settings, use:

- Branch: `master`
- Folder: `/docs`

After you push changes to GitHub, GitHub Pages serves the files from `docs/`.

## Set Up Automatic Refreshes With cron-job.org

Use cron-job.org as the scheduler that tells GitHub to run the update workflow.

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

Save this token somewhere safe as soon as GitHub shows it. GitHub may only show the full token one time.

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

In cron-job.org, headers are not entered as one line each. Use the separate header name and header value input boxes.

Add these three headers:

| Header name | Header value |
| --- | --- |
| `Accept` | `application/vnd.github+json` |
| `Authorization` | `Bearer YOUR_GITHUB_TOKEN` |
| `Content-Type` | `application/json` |

Replace `YOUR_GITHUB_TOKEN` with the token you created.

#### 4. Add request body

Use this request body:

```json
{"ref":"master"}
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

## Technical Reference

For data sources, refresh behavior, generated files, and manual league-data details, see `TECHNICAL-REFERENCE.md`. Use that file when you need the project internals.

## Maintainers

See `MAINTAINING.md` for rollback instructions, artifact contracts, deploy checks, cache-busting policy, and latest-changes modal rules.
