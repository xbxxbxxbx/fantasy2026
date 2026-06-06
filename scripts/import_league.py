#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from update_data_lib.config import load_config
from update_data_lib.constants import LEAGUE_PATH
from update_data_lib.fetchers import fetch_html
from update_data_lib.parsers import parse_poker_org_team_page


def read_urls(path: Path) -> list[str]:
    urls = []
    seen = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        if not value.startswith(("http://", "https://")):
            raise ValueError(f"{path}:{line_number} is not a URL: {value}")
        if value not in seen:
            urls.append(value)
            seen.add(value)
    return urls


def default_league_name() -> str:
    try:
        config = load_config()
    except Exception:
        return "Poker Fantasy Leaderboard"
    return str(config.get("leagueName") or "Poker Fantasy Leaderboard")


def import_teams(urls: list[str]) -> list[dict]:
    teams = []
    for index, url in enumerate(urls, start=1):
        print(f"[{index}/{len(urls)}] Fetching {url}", file=sys.stderr)
        html = fetch_html(url)
        team = parse_poker_org_team_page(html, url)
        print(
            f"  imported {team['teamName']} ({len(team['roster'])} players)",
            file=sys.stderr,
        )
        teams.append(team)
    return teams


def build_payload(teams: list[dict], league_name: str | None = None) -> dict:
    return {
        "leagueName": league_name or default_league_name(),
        "teams": teams,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import league rosters from a text file of Poker.org team URLs."
    )
    parser.add_argument("url_file", type=Path, help="Text file with one Poker.org team URL per line")
    parser.add_argument(
        "--league-name",
        default=None,
        help="Optional league name to write to league.json",
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
        urls = read_urls(args.url_file)
        if not urls:
            raise ValueError(f"No URLs found in {args.url_file}")

        teams = import_teams(urls)
        payload = build_payload(teams, args.league_name)
        output = json.dumps(payload, indent=2) + "\n"

        if args.dry_run:
            print(output, end="")
        else:
            args.output.write_text(output, encoding="utf-8")
            print(f"Wrote {args.output}")
            print(f"Imported {len(teams)} teams")
    except Exception as exc:
        print(f"Failed to import league: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
