#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "docs" / "config.js"
OUTPUT_PATH = ROOT / "docs" / "data.json"


class ConfigError(RuntimeError):
    pass


@dataclass
class TeamSource:
    manager_name: str
    team_name: str
    url: str


class DraftTableParser(HTMLParser):
    def __init__(self, expected_table_class: str) -> None:
        super().__init__()
        self.expected_table_class = expected_table_class
        self.in_target_table = False
        self.table_depth = 0
        self.capture_cell = False
        self.current_row: list[str] = []
        self.current_cell: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "table":
            classes = (attrs_dict.get("class") or "").split()
            if self.expected_table_class in classes and not self.in_target_table:
                self.in_target_table = True
                self.table_depth = 1
                return
            if self.in_target_table:
                self.table_depth += 1
        elif self.in_target_table and tag == "tr":
            self.current_row = []
        elif self.in_target_table and tag in {"td", "th"}:
            self.capture_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        if self.in_target_table and tag in {"td", "th"} and self.capture_cell:
            cell_text = unescape("".join(self.current_cell))
            cell_text = re.sub(r"\s+", " ", cell_text).strip()
            self.current_row.append(cell_text)
            self.capture_cell = False
        elif self.in_target_table and tag == "tr" and self.current_row:
            self.rows.append(self.current_row)
            self.current_row = []
        elif self.in_target_table and tag == "table":
            self.table_depth -= 1
            if self.table_depth <= 0:
                self.in_target_table = False

    def handle_data(self, data: str) -> None:
        if self.capture_cell:
            self.current_cell.append(data)


def load_config() -> dict:
    text = CONFIG_PATH.read_text(encoding="utf-8")
    match = re.search(r"window\.LEADERBOARD_CONFIG\s*=\s*(\{.*\});?\s*$", text, re.S)
    if not match:
        raise ConfigError(f"Could not parse config object from {CONFIG_PATH}")

    config_text = match.group(1)
    config_text = re.sub(
        r'([{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:',
        r'\1"\2":',
        config_text,
    )
    config_text = re.sub(r",(\s*[}\]])", r"\1", config_text)
    return json.loads(config_text)


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_team_page(html: str, table_class: str, player_column: str, score_column: str) -> list[dict]:
    parser = DraftTableParser(table_class)
    parser.feed(html)

    if len(parser.rows) < 2:
        raise ValueError("No rows found in target draft table")

    headers = parser.rows[0]
    try:
        player_index = headers.index(player_column)
        score_index = headers.index(score_column)
    except ValueError as exc:
        raise ValueError(f"Missing expected columns in table headers: {headers}") from exc

    players = []
    for row in parser.rows[1:]:
        if len(row) <= max(player_index, score_index):
            continue

        player_name = row[player_index].strip()
        score_text = row[score_index].strip()
        if not player_name or player_name == player_column:
            continue

        try:
            score_value = float(score_text or 0)
        except ValueError:
            continue

        players.append(
            {
                "player": player_name,
                "points": score_value,
            }
        )

    return players


def build_snapshot(config: dict) -> dict:
    table_selector = config.get("teamPageTableSelector", ".draft-player-table")
    table_class = table_selector.lstrip(".")
    player_column = config.get("teamPagePlayerColumn", "PLAYER")
    score_column = config.get("teamPagePointsColumn", "SCORE")

    results = []
    failures = []

    for entry in config.get("teamSources", []):
        source = TeamSource(
            manager_name=entry["managerName"],
            team_name=entry["teamName"],
            url=entry["url"],
        )
        try:
            html = fetch_html(source.url)
            players = parse_team_page(html, table_class, player_column, score_column)
            total_points = sum(player["points"] for player in players)
            results.append(
                {
                    "managerName": source.manager_name,
                    "teamName": source.team_name,
                    "url": source.url,
                    "players": sorted(players, key=lambda item: item["points"], reverse=True),
                    "totalPoints": round(total_points, 2),
                }
            )
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            failures.append(
                {
                    "managerName": source.manager_name,
                    "teamName": source.team_name,
                    "url": source.url,
                    "error": str(exc),
                }
            )

    results.sort(key=lambda item: item["totalPoints"], reverse=True)

    return {
        "leagueName": config.get("leagueName", "Poker Fantasy Leaderboard"),
        "leagueDescription": config.get("leagueDescription", ""),
        "scoringLabel": config.get("scoringLabel", "Score"),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "managers": results,
        "failures": failures,
    }


def main() -> int:
    try:
        config = load_config()
        snapshot = build_snapshot(config)
        OUTPUT_PATH.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"Failed to update data: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
