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
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "docs" / "config.js"
OUTPUT_PATH = ROOT / "docs" / "data.json"
HISTORY_DIR = ROOT / "docs" / "history"
DISPLAY_TIMEZONE = ZoneInfo("America/New_York")


class ConfigError(RuntimeError):
    pass


@dataclass
class TeamSource:
    manager_name: str
    team_name: str
    url: str
    roster: list[str]


class DraftTableParser(HTMLParser):
    def __init__(self, expected_table_class: str | None = None, expected_table_id: str | None = None) -> None:
        super().__init__()
        self.expected_table_class = expected_table_class
        self.expected_table_id = expected_table_id
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
            matches_class = self.expected_table_class and self.expected_table_class in classes
            matches_id = self.expected_table_id and attrs_dict.get("id") == self.expected_table_id
            if (matches_class or matches_id) and not self.in_target_table:
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
    parts = urlsplit(url)
    referer = f"{parts.scheme}://{parts.netloc}/" if parts.scheme and parts.netloc else url
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
        "Referer": referer,
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


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def snapshot_totals(snapshot: dict) -> dict[str, float]:
    totals = {}
    for manager in snapshot.get("managers", []):
        manager_name = manager.get("managerName")
        total_points = manager.get("totalPoints")
        if manager_name is None or total_points is None:
            continue
        totals[str(manager_name)] = float(total_points)
    return totals


def current_local_date() -> str:
    return datetime.now(timezone.utc).astimezone(DISPLAY_TIMEZONE).date().isoformat()


def snapshot_local_date(snapshot: dict) -> str | None:
    generated_at = snapshot.get("generatedAt")
    if not generated_at:
        return None

    try:
        timestamp = datetime.fromisoformat(str(generated_at))
    except ValueError:
        return None

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return timestamp.astimezone(DISPLAY_TIMEZONE).date().isoformat()


def history_path_for(date_key: str) -> Path:
    return HISTORY_DIR / f"{date_key}.json"


def load_daily_baseline(previous_snapshot: dict) -> tuple[dict, str]:
    today_key = current_local_date()
    baseline_path = history_path_for(today_key)
    existing_baseline = load_json(baseline_path)
    if existing_baseline:
        return existing_baseline, today_key

    previous_date = snapshot_local_date(previous_snapshot)
    if previous_snapshot and previous_snapshot.get("managers"):
        if previous_date != today_key:
            return previous_snapshot, today_key
        return previous_snapshot, today_key

    return {}, today_key


def write_daily_baseline(today_key: str, baseline_snapshot: dict) -> None:
    if not baseline_snapshot:
        return

    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    path = history_path_for(today_key)
    if not path.exists():
        path.write_text(json.dumps(baseline_snapshot, indent=2) + "\n", encoding="utf-8")


def parse_score_feed(
    html: str,
    table_id: str,
    player_column: str,
    score_column: str,
) -> dict[str, float]:
    parser = DraftTableParser(expected_table_id=table_id)
    parser.feed(html)

    if len(parser.rows) < 2:
        raise ValueError("No rows found in target score table")

    headers = parser.rows[0]
    try:
        player_index = headers.index(player_column)
        score_index = headers.index(score_column)
    except ValueError as exc:
        raise ValueError(f"Missing expected columns in table headers: {headers}") from exc

    scores: dict[str, float] = {}
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

        scores[player_name] = score_value

    return scores


def build_snapshot(config: dict) -> dict:
    score_feed_url = config["scoreFeedUrl"]
    table_id = config.get("scoreFeedTableId", "dataTable-main")
    player_column = config.get("scoreFeedPlayerColumn", "Player")
    score_column = config.get("scoreFeedPointsColumn", "Score")
    previous_snapshot = load_previous_snapshot()
    previous_totals = load_previous_totals()
    daily_baseline_snapshot, comparison_date = load_daily_baseline(previous_snapshot)
    baseline_totals = snapshot_totals(daily_baseline_snapshot)
    previous_managers = {
        manager.get("managerName"): manager
        for manager in previous_snapshot.get("managers", [])
        if manager.get("managerName")
    }

    results = []
    failures = []
    success_count = 0

    try:
        html = fetch_html(score_feed_url)
        score_map = parse_score_feed(html, table_id, player_column, score_column)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        failures.append(
            {
                "managerName": "score-feed",
                "teamName": "score-feed",
                "url": score_feed_url,
                "error": str(exc),
            }
        )
        score_map = None

    for entry in config.get("teamSources", []):
        source = TeamSource(
            manager_name=entry["managerName"],
            team_name=entry["teamName"],
            url=entry["url"],
            roster=entry["roster"],
        )
        try:
            if score_map is None:
                raise ValueError("Score feed unavailable")
            players = [
                {
                    "player": player_name,
                    "points": score_map.get(player_name, 0.0),
                }
                for player_name in source.roster
            ]
            total_points = sum(player["points"] for player in players)
            results.append(
                {
                    "managerName": source.manager_name,
                    "teamName": source.team_name,
                    "url": source.url,
                    "players": sorted(players, key=lambda item: item["points"], reverse=True),
                    "totalPoints": round(total_points, 2),
                    "pointsChange": round(total_points - baseline_totals.get(source.manager_name, total_points), 2),
                    "pointsChangeSincePrevious": round(
                        total_points - previous_totals.get(source.manager_name, total_points),
                        2,
                    ),
                }
            )
            success_count += 1
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            if score_map is not None:
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
                fallback_manager["pointsChangeSincePrevious"] = 0.0
                fallback_manager["stale"] = True
                fallback_manager["staleReason"] = str(exc)
                results.append(fallback_manager)

    results.sort(key=lambda item: item["totalPoints"], reverse=True)

    snapshot = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "pointsChangeLabel": "today",
        "pointsChangeComparisonDate": comparison_date,
        "managers": results,
        "failures": failures,
        "successCount": success_count,
    }
    if success_count > 0:
        write_daily_baseline(comparison_date, daily_baseline_snapshot or previous_snapshot or snapshot)

    return snapshot


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
