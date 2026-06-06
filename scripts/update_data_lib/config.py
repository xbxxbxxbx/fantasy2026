from __future__ import annotations

import json
from dataclasses import dataclass

from .constants import CONFIG_PATH, CONFIG_SCRIPT_PATH, LEAGUE_PATH


class ConfigError(RuntimeError):
    pass


@dataclass
class TeamSource:
    manager_name: str
    team_name: str
    url: str
    roster: list[str]


PUBLIC_CONFIG_KEYS = (
    "leagueName",
    "sourceLabel",
    "sourceUrl",
    "updateCadenceLabel",
    "liveSweatsTimeGateEnabled",
    "scoringLabel",
)


def _load_app_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Missing app config file: {CONFIG_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Could not parse app config from {CONFIG_PATH}") from exc


def _load_league_config() -> dict:
    try:
        return json.loads(LEAGUE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Could not parse league definition from {LEAGUE_PATH}") from exc


def _normalize_team_source(entry: dict) -> dict:
    team_name = str(entry.get("teamName") or entry.get("managerName") or "").strip()
    manager_name = str(entry.get("managerName") or team_name).strip()
    return {
        "managerName": manager_name,
        "teamName": team_name or manager_name,
        "url": str(entry.get("url") or "").strip(),
        "roster": list(entry.get("roster") or []),
    }


def load_config() -> dict:
    app_config = _load_app_config()
    league_config = _load_league_config()
    merged = dict(app_config)
    merged["leagueName"] = league_config.get("leagueName") or app_config.get("leagueName")
    merged["teamSources"] = [
        _normalize_team_source(entry)
        for entry in league_config.get("teams", [])
        if entry.get("roster")
    ]
    return merged


def public_config(config: dict) -> dict:
    return {key: config[key] for key in PUBLIC_CONFIG_KEYS if key in config}


def build_config_script(config: dict) -> str:
    payload = json.dumps(public_config(config), indent=2, sort_keys=True)
    payload_lines = payload.splitlines()
    formatted_payload = "\n".join(
        [payload_lines[0], *(f"  {line}" for line in payload_lines[1:])]
    )
    return (
        "(function (window) {\n"
        f"  window.LEADERBOARD_CONFIG = {formatted_payload};\n"
        "  window.LEADERBOARD_CONFIG_READY = Promise.resolve(window.LEADERBOARD_CONFIG);\n"
        "})(window);\n"
    )


def write_config_script(config: dict) -> None:
    script = build_config_script(config)
    if CONFIG_SCRIPT_PATH.exists() and CONFIG_SCRIPT_PATH.read_text(encoding="utf-8") == script:
        return
    CONFIG_SCRIPT_PATH.write_text(script, encoding="utf-8")
