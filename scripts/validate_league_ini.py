#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

from update_data_lib.constants import SETTINGS_PATH
from update_data_lib.league_import import (
    LEAGUE_SECTION,
    URLS_SECTION,
    is_poker_org_team_url,
    read_ini_settings,
)


def validate_required_fields(path: Path) -> list[str]:
    try:
        settings = read_ini_settings(path)
    except Exception as exc:
        return [str(exc)]

    errors = []
    if not settings.league_name:
        errors.append(f"Missing [{LEAGUE_SECTION}] name in {path.name}")
    if not settings.urls:
        errors.append(f"Add at least one Poker.org URL under [{URLS_SECTION}] in {path.name}")
    for url in settings.urls:
        if not is_poker_org_team_url(url):
            errors.append(
                f"Use Poker.org team page URLs under [{URLS_SECTION}] in {path.name}: {url}"
            )
    return errors


def main() -> int:
    path = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else SETTINGS_PATH

    if not path.exists():
        print(f"Missing settings file: {path}", file=sys.stderr)
        return 1

    errors = validate_required_fields(path)
    if errors:
        print("league.ini validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    settings = read_ini_settings(path)
    count = len(settings.urls)
    plural = "" if count == 1 else "s"
    print(f"OK: {path.name} has a league name and {count} Poker.org URL{plural}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
