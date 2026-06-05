from __future__ import annotations

from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

from .config import TeamSource
from .fetchers import fetch_html, fetch_json
from .history import (
    load_daily_baseline,
    load_previous_snapshot,
    load_previous_totals,
    snapshot_totals,
    write_daily_baseline,
)
from .parsers import LinkedTableParser, extract_csrf_token, parse_score_feed


def fetch_active_players_snapshot() -> dict:
    sweat_page_url = "https://www.25kfantasy.com/sweat"
    sweat_api_url = "https://www.25kfantasy.com/process/sweat"
    page_html = fetch_html(sweat_page_url)
    csrf_token = extract_csrf_token(page_html)
    response = fetch_json(
        sweat_api_url,
        {"q": "sweat_all_active", "league": "25k"},
        headers={"X-CSRF-Token": csrf_token},
    )

    if response.get("status") != "success":
        raise ValueError(response.get("message") or "Active players request failed")

    results_html = response.get("data", {}).get("results", "")
    parser = LinkedTableParser()
    parser.feed(results_html)
    if len(parser.rows) < 2:
        raise ValueError("No rows found in active players table")

    headers = [cell["text"] for cell in parser.rows[0]]
    header_map = {header.lower(): index for index, header in enumerate(headers)}
    players = []
    for row in parser.rows[1:]:
        if len(row) < len(headers):
            continue

        points_text = row[header_map["points"]]["text"].strip() if "points" in header_map else "0"
        try:
            points_value = float(points_text)
        except ValueError:
            points_value = 0.0

        event_href = row[header_map["event"]]["href"].strip() if "event" in header_map else ""
        if event_href.startswith("/"):
            event_href = f"https://www.25kfantasy.com{event_href}"

        player = {
            "player": row[header_map["player"]]["text"].strip() if "player" in header_map else "",
            "event": row[header_map["event"]]["text"].strip() if "event" in header_map else "",
            "eventUrl": event_href,
            "team": row[header_map["team"]]["text"].strip() if "team" in header_map else "",
            "rank": row[header_map["rank"]]["text"].strip() if "rank" in header_map else "",
            "chips": row[header_map["chips"]]["text"].strip() if "chips" in header_map else "",
            "bb": row[header_map["bb"]]["text"].strip() if "bb" in header_map else "",
            "bonus": row[header_map["bonus"]]["text"].strip() if "bonus" in header_map else "",
            "points": points_value,
        }
        if player["player"]:
            players.append(player)

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "league": "25k",
        "count": len(players),
        "players": players,
    }


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
                    "pointsChange": round(
                        total_points - baseline_totals.get(source.manager_name, total_points), 2
                    ),
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
        "leagueName": config.get("leagueName"),
        "sourceLabel": config.get("sourceLabel"),
        "sourceUrl": config.get("sourceUrl"),
        "updateCadenceLabel": config.get("updateCadenceLabel"),
        "pointsChangeLabel": "since restart",
        "pointsChangeComparisonDate": comparison_date,
        "managers": results,
        "failures": failures,
        "successCount": success_count,
    }
    if success_count > 0:
        write_daily_baseline(
            comparison_date,
            daily_baseline_snapshot or snapshot,
        )

    return snapshot
