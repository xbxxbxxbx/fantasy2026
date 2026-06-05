from __future__ import annotations

import json
import re
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


def _load_js_config() -> dict:
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


def _load_league_config() -> dict:
    try:
        return json.loads(LEAGUE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Missing league definition file: {LEAGUE_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Could not parse league definition from {LEAGUE_PATH}") from exc


def load_config() -> dict:
    app_config = _load_js_config()
    league_config = _load_league_config()
    merged = dict(app_config)
    merged["leagueName"] = league_config.get("leagueName") or app_config.get("leagueName")
    merged["teamSources"] = league_config.get("teams", [])
    return merged
