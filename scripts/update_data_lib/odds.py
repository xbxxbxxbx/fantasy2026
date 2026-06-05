from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path


SIMULATION_COUNT = 6000
PLAYER_HISTORY_WEIGHT = 0.1
REMAINING_UPSIDE_WEIGHT = 0.6


def load_player_history(path: Path) -> dict[str, list[float]]:
    if not path.exists():
        return {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    history: dict[str, list[float]] = {}
    for player_name, seasons in payload.items():
        if not isinstance(seasons, dict):
            continue

        yearly_entries = []
        for year, points in seasons.items():
            try:
                yearly_entries.append((int(year), float(points)))
            except (TypeError, ValueError):
                continue
        yearly_entries.sort(key=lambda item: item[0])

        recent_samples = [points for year, points in yearly_entries if year >= 2022]
        all_samples = [points for _, points in yearly_entries]
        samples = recent_samples if len(recent_samples) >= 2 else all_samples
        if samples:
            history[str(player_name).strip()] = samples

    return history


def probability_to_american_odds(probability: float) -> int | None:
    if probability <= 0 or probability >= 1:
        return None
    if probability >= 0.5:
        return round((-100 * probability) / (1 - probability))
    return round((100 * (1 - probability)) / probability)


def managers_have_odds(managers: list[dict]) -> bool:
    return all(
        "titleWinProbability" in manager and "titleAmericanOdds" in manager
        for manager in managers
    )


def snapshot_has_player_point_updates(previous_snapshot: dict, managers: list[dict]) -> bool:
    previous_managers = {
        str(manager.get("managerName")): manager
        for manager in previous_snapshot.get("managers", [])
        if manager.get("managerName")
    }
    if len(previous_managers) != len(managers):
        return True

    for manager in managers:
        manager_name = str(manager.get("managerName") or "")
        previous_manager = previous_managers.get(manager_name)
        if not previous_manager:
            return True

        previous_points = {
            str(player.get("player") or ""): float(player.get("points", 0))
            for player in previous_manager.get("players", [])
        }
        current_points = {
            str(player.get("player") or ""): float(player.get("points", 0))
            for player in manager.get("players", [])
        }
        if previous_points != current_points:
            return True

    return False


def copy_previous_odds(previous_snapshot: dict, managers: list[dict]) -> None:
    previous_managers = {
        str(manager.get("managerName")): manager
        for manager in previous_snapshot.get("managers", [])
        if manager.get("managerName")
    }
    for manager in managers:
        previous_manager = previous_managers.get(str(manager.get("managerName") or ""))
        if not previous_manager:
            continue
        if "titleWinProbability" in previous_manager:
            manager["titleWinProbability"] = previous_manager["titleWinProbability"]
        if "titleAmericanOdds" in previous_manager:
            manager["titleAmericanOdds"] = previous_manager["titleAmericanOdds"]


def apply_title_odds(
    managers: list[dict],
    player_history_by_name: dict[str, list[float]],
) -> None:
    if not managers:
        return

    pooled_samples = [
        sample
        for samples in player_history_by_name.values()
        for sample in samples
    ]
    if not pooled_samples:
        uniform_probability = 1 / len(managers)
        for manager in managers:
            manager["titleWinProbability"] = round(uniform_probability, 6)
            manager["titleAmericanOdds"] = probability_to_american_odds(uniform_probability)
        return

    seed_payload = json.dumps(
        [
            {
                "managerName": manager.get("managerName"),
                "totalPoints": manager.get("totalPoints"),
                "players": [
                    {"player": player.get("player"), "points": player.get("points")}
                    for player in manager.get("players", [])
                ],
            }
            for manager in managers
        ],
        sort_keys=True,
    )
    seed = int(hashlib.sha256(seed_payload.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)

    league_remaining_cache: dict[float, list[float]] = {}
    player_remaining_cache: dict[tuple[str, float], list[float]] = {}
    win_shares = {str(manager.get("managerName")): 0.0 for manager in managers}

    def get_league_remaining_samples(current_points: float) -> list[float]:
        cached = league_remaining_cache.get(current_points)
        if cached is None:
            cached = [max(0.0, sample - current_points) for sample in pooled_samples]
            league_remaining_cache[current_points] = cached
        return cached

    def get_player_remaining_samples(player_name: str, current_points: float) -> list[float]:
        cache_key = (player_name, current_points)
        cached = player_remaining_cache.get(cache_key)
        if cached is None:
            samples = player_history_by_name.get(player_name, [])
            cached = [max(0.0, sample - current_points) for sample in samples]
            player_remaining_cache[cache_key] = cached
        return cached

    def draw_remaining_points(player_name: str, current_points: float) -> float:
        player_remaining_samples = get_player_remaining_samples(player_name, current_points)
        league_remaining_samples = get_league_remaining_samples(current_points)
        sample_pool = (
            player_remaining_samples
            if player_remaining_samples and rng.random() < PLAYER_HISTORY_WEIGHT
            else league_remaining_samples
        )
        return REMAINING_UPSIDE_WEIGHT * rng.choice(sample_pool)

    for _ in range(SIMULATION_COUNT):
        totals = []
        for manager in managers:
            total = 0.0
            for player in manager.get("players", []):
                current_points = float(player.get("points", 0))
                total += current_points + draw_remaining_points(
                    str(player.get("player") or "").strip(),
                    current_points,
                )
            totals.append((str(manager.get("managerName")), total))

        best_total = max(total for _, total in totals)
        winners = [manager_name for manager_name, total in totals if total == best_total]
        share = 1 / len(winners)
        for winner in winners:
            win_shares[winner] += share

    for manager in managers:
        manager_name = str(manager.get("managerName") or "")
        win_probability = win_shares.get(manager_name, 0.0) / SIMULATION_COUNT
        manager["titleWinProbability"] = round(win_probability, 6)
        manager["titleAmericanOdds"] = probability_to_american_odds(win_probability)
