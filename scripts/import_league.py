#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from update_data_lib.constants import LEAGUE_PATH, SETTINGS_PATH
from update_data_lib.league_import import (
    build_payload,
    import_league_from_settings,
    import_teams,
    read_import_settings,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import league rosters from a league.ini settings file."
    )
    parser.add_argument(
        "settings_file",
        nargs="?",
        type=Path,
        default=SETTINGS_PATH,
        help=f"INI settings file, defaults to {SETTINGS_PATH}",
    )
    parser.add_argument(
        "--league-name",
        default=None,
        help="Optional league name override to write to league.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=LEAGUE_PATH,
        help=f"Output path, defaults to {LEAGUE_PATH}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated league JSON without writing it",
    )
    args = parser.parse_args()

    try:
        if not args.dry_run:
            payload = import_league_from_settings(args.settings_file, args.output, args.league_name)
        else:
            settings = read_import_settings(args.settings_file)
            if not settings.urls:
                raise ValueError(f"No URLs found in {args.settings_file}")
            teams = import_teams(settings.urls)
            payload = build_payload(
                teams,
                args.league_name or settings.league_name,
                args.settings_file if settings.signature else None,
                settings.signature,
            )
        output = json.dumps(payload, indent=2) + "\n"

        if args.dry_run:
            print(output, end="")
        else:
            print(f"Wrote {args.output}")
            print(f"Imported {len(payload.get('teams', []))} teams")
    except Exception as exc:
        print(f"Failed to import league: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
