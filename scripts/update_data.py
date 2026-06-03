#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
import time
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
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.poker.org/",
    }
    retry_delays = [0, 2, 5]

    last_error: Exception | None = None
    for delay in retry_delays:
        if delay:
            time.sleep(delay)

        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {403, 429}:
                raise
        except URLError as exc:
            last_error = exc

    if last_error:
        raise last_error
    raise RuntimeError(f"Failed to fetch {url}")


def load_previous_totals() -> dict[str, float]:
    if not OUTPUT_PATH.exists():
        return {}

    try:
        payload = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    totals = {}
    for manager in payload.get("managers", []):
        manager_name = manager.get("managerName")
        total_points = manager.get("totalPoints")
        if manager_name is None or total_points is None:
            continue
        totals[str(manager_name)] = float(total_points)
    return totals


def load_previous_snapshot() -> dict:
    if not OUTPUT_PATH.exists():
        return {}

    try:
        return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


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
    previous_snapshot = load_previous_snapshot()
    previous_totals = load_previous_totals()
    previous_managers = {
        manager.get("managerName"): manager
        for manager in previous_snapshot.get("managers", [])
        if manager.get("managerName")
    }

    results = []
    failures = []
    success_count = 0

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
                    "pointsChange": round(total_points - previous_totals.get(source.manager_name, total_points), 2),
                }
            )
            success_count += 1
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            failures.append(
                {
                    "managerName": source.manager_name,
                    "teamName": source.team_name,
                    "url": source.url,
                    "error": str(exc),
                }
            )
            previous_manager = previous_managers.get(source.manager_name)
            if previous_manager:
                fallback_manager = dict(previous_manager)
                fallback_manager["pointsChange"] = 0.0
                fallback_manager["stale"] = True
                fallback_manager["staleReason"] = str(exc)
                results.append(fallback_manager)

    results.sort(key=lambda item: item["totalPoints"], reverse=True)

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "managers": results,
        "failures": failures,
        "successCount": success_count,
    }


def main() -> int:
    try:
        config = load_config()
        snapshot = build_snapshot(config)
        if snapshot.get("successCount", 0) == 0:
            raise RuntimeError("All team scrapes failed; preserving previous snapshot.")
        snapshot.pop("successCount", None)
        OUTPUT_PATH.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"Failed to update data: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
