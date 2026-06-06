#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from update_data_lib.constants import ROOT, SETUP_LOG_PATH


def reset_log() -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    SETUP_LOG_PATH.write_text(
        f"Quickstart setup log\nStarted: {timestamp}\n\n",
        encoding="utf-8",
    )


def append_log(message: str) -> None:
    with SETUP_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(message)


def run_logged_step(title: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    append_log(f"== {title} ==\n$ {' '.join(command)}\n")
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    if output:
        append_log(output)
        if not output.endswith("\n"):
            append_log("\n")
    append_log(f"Exit code: {result.returncode}\n\n")
    return result


def main() -> int:
    reset_log()

    print("Validating league.ini...")
    validation = run_logged_step(
        "Validate league.ini",
        [sys.executable, "scripts/validate_league_ini.py"],
    )
    if validation.returncode != 0:
        print("Setup stopped. Open setup.log for details, then fix league.ini and try again.")
        return 1

    print("Updating site data...")
    update = run_logged_step(
        "Update site data",
        [sys.executable, "scripts/update_data.py"],
    )
    if update.returncode != 0:
        print("Setup stopped. Open setup.log for details, then fix the issue and try again.")
        return 1
    update_output = update.stdout + update.stderr
    if "Warning:" in update_output:
        append_log("Quickstart treats update warnings as a setup failure.\n")
        print("Setup stopped. Open setup.log for details, then fix the issue and try again.")
        return 1

    append_log(
        "Quickstart setup completed.\n"
        "Start preview separately with: python3 -m http.server 4181 --directory docs\n"
    )
    print("Setup finished.")
    print("Start preview separately with: python3 -m http.server 4181 --directory docs")
    print(f"Debug details are in {SETUP_LOG_PATH.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
