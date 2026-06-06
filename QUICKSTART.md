# Quickstart Workflow

Use this file when you want Codex to guide setup in checkpoints with a real setup command instead of relying on loose prose.

Goal:

- run one deterministic setup command
- validate `league.ini`
- pause if the file needs fixes
- continue after the user replies
- update site data
- start a local preview with a direct command
- leave the user ready to publish

## Workflow

1. Run setup.

Run:

```bash
python3 scripts/quickstart_setup.py
```

You can also run the same setup in GitHub Actions with `.github/workflows/setup-league.yml`.

This command:

- validates `league.ini`
- writes debug output to `setup.log`
- runs `scripts/update_data.py`
- stops if validation or data update is incomplete

2. If setup fails, read `setup.log` first.

Do not guess.

Use `setup.log` to identify the failing step and the exact error text. If the log is not enough, inspect the related file or command directly before replying.

If setup was run in GitHub Actions, open the `setup-log` artifact from that workflow run. It is overwritten on every run because the workflow starts from a fresh checkout and `scripts/quickstart_setup.py` resets the file before doing any work.

3. Fix small file problems yourself when safe.

Examples:

- extra quote marks around a URL
- a UTF-8 byte-order mark at the top of `league.ini`
- a missing `name = ...` value you can clearly recover from the existing file context

After a safe fix, rerun:

```bash
python3 scripts/quickstart_setup.py
```

4. After setup succeeds, start preview as a separate direct command.

Run:

```bash
python3 -m http.server 4181 --directory docs
```

If port `4181` is already in use, try the next port:

```bash
python3 -m http.server 4182 --directory docs
```

Then continue with the exact working URL, for example `http://127.0.0.1:4182/index.html`.

Do not ask the Python setup script to launch preview itself. In Codex, starting the preview server is more reliable as a direct command.

5. If the user needs to make a change, stop and respond in a strict format.

Requirements for the response:

- include a Codex file link to the file they need to edit
- keep the instructions short
- use one bold summary header per resolution
- put numbered steps under each header
- if the app exposes a native confirmation control, use it for the continue step
- otherwise tell them to reply `Continue` when they are done

Example shape:

**Fix `league.ini`**
1. Open `league.ini`.
2. Replace the bad URL with the Poker.org team page URL.
3. Click the continue control if one is shown. Otherwise reply `Continue`.

6. If setup and preview both succeed, finish with the publish-ready handoff.

Tell the user:

- the exact preview URL
- that setup completed
- that `setup.log` contains debug details if they need them later
- that they are ready to publish with GitHub Pages
- that they should follow the `cron-job.org` section in `README.md` for automatic refreshes

## Notes

- `league.ini` is not valid unless it has all of these:
  - `[League]` `name`
  - at least one URL under `[Poker.org URLs]`
  - every URL points to a Poker.org fantasy team page
- The pause/continue step should use a normal Codex reply and the user’s next message.
- If the app exposes a native confirmation widget or choice control, use it for the continue step. Otherwise use a simple `Continue` reply.
- `setup.log` lives in the project root.
