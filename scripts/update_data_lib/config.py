from __future__ import annotations

import json
from dataclasses import dataclass

from .constants import CONFIG_PATH, LEAGUE_PATH


class ConfigError(RuntimeError):
    pass


@dataclass
class TeamSource:
    manager_name: str
    team_name: str
    url: str
    roster: list[str]


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
    except FileNotFoundError as exc:
        raise ConfigError(f"Missing league definition file: {LEAGUE_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Could not parse league definition from {LEAGUE_PATH}") from exc


def load_config() -> dict:
    app_config = _load_app_config()
    league_config = _load_league_config()
    merged = dict(app_config)
    merged["leagueName"] = league_config.get("leagueName") or app_config.get("leagueName")
    merged["teamSources"] = league_config.get("teams", [])
    return merged
