from __future__ import annotations

import json
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from .constants import DISPLAY_TIMEZONE, HISTORY_DIR, OUTPUT_PATH

POKER_DAY_RESET_HOUR = 10


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_previous_snapshot() -> dict:
    return load_json(OUTPUT_PATH)


def load_previous_totals() -> dict[str, float]:
    payload = load_previous_snapshot()
    totals = {}
    for manager in payload.get("managers", []):
        manager_name = manager.get("managerName")
        total_points = manager.get("totalPoints")
        if manager_name is None or total_points is None:
            continue
        totals[str(manager_name)] = float(total_points)
    return totals


def snapshot_totals(snapshot: dict) -> dict[str, float]:
    totals = {}
    for manager in snapshot.get("managers", []):
        manager_name = manager.get("managerName")
        total_points = manager.get("totalPoints")
        if manager_name is None or total_points is None:
            continue
        totals[str(manager_name)] = float(total_points)
    return totals


def poker_day_key_for(timestamp: datetime) -> str:
    local_timestamp = timestamp.astimezone(DISPLAY_TIMEZONE)
    reset_boundary = datetime.combine(
        local_timestamp.date(),
        time(hour=POKER_DAY_RESET_HOUR),
        tzinfo=DISPLAY_TIMEZONE,
    )
    if local_timestamp < reset_boundary:
        local_timestamp -= timedelta(days=1)
    return local_timestamp.date().isoformat()


def current_poker_day_key() -> str:
    return poker_day_key_for(datetime.now(timezone.utc))


def snapshot_poker_day_key(snapshot: dict) -> str | None:
    generated_at = snapshot.get("generatedAt")
    if not generated_at:
        return None

    try:
        timestamp = datetime.fromisoformat(str(generated_at))
    except ValueError:
        return None

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return poker_day_key_for(timestamp)


def history_path_for(date_key: str) -> Path:
    return HISTORY_DIR / f"{date_key}.json"


def load_daily_baseline(previous_snapshot: dict) -> tuple[dict, str]:
    today_key = current_poker_day_key()
    baseline_path = history_path_for(today_key)
    existing_baseline = load_json(baseline_path)
    if existing_baseline and snapshot_poker_day_key(existing_baseline) == today_key:
        return existing_baseline, today_key

    return {}, today_key


def write_daily_baseline(today_key: str, baseline_snapshot: dict) -> None:
    if not baseline_snapshot:
        return

    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    path = history_path_for(today_key)
    existing_baseline = load_json(path)
    if not existing_baseline or snapshot_poker_day_key(existing_baseline) != today_key:
        path.write_text(json.dumps(baseline_snapshot, indent=2) + "\n", encoding="utf-8")
