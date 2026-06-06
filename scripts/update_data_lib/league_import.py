from __future__ import annotations

import configparser
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .config import load_config
from .constants import LEAGUE_PATH, SETTINGS_PATH
from .fetchers import fetch_html
from .parsers import parse_poker_org_team_page

URLS_SECTION = "Poker.org URLs"
LEAGUE_SECTION = "League"


@dataclass(frozen=True)
class ImportSettings:
    league_name: str | None
    urls: list[str]
    signature: str | None = None


def validate_url(value: str, path: Path, line_number: int | None = None) -> str:
    url = value.strip()
    for left_quote, right_quote in (('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’")):
        if url.startswith(left_quote) and url.endswith(right_quote) and len(url) >= 2:
            url = url[1:-1].strip()
            break
    if not url.startswith(("http://", "https://")):
        location = f"{path}:{line_number}" if line_number else str(path)
        raise ValueError(f"{location} is not a URL: {value}")
    return url


def is_poker_org_team_url(url: str) -> bool:
    parts = urlsplit(url)
    host = parts.netloc.lower()
    path = parts.path.lower().rstrip("/")
    return host in {"poker.org", "www.poker.org"} and "/fantasy/" in path and "/team/" in path


def read_urls(path: Path) -> list[str]:
    urls = []
    seen = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        url = validate_url(value, path, line_number)
        if url not in seen:
            urls.append(url)
            seen.add(url)
    return urls


def settings_signature(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_ini_settings(path: Path) -> ImportSettings:
    parser = configparser.ConfigParser(
        allow_no_value=True,
        delimiters=("=",),
        interpolation=None,
        strict=False,
    )
    parser.optionxform = str

    try:
        with path.open(encoding="utf-8-sig") as settings_file:
            parser.read_file(settings_file)
    except configparser.Error as exc:
        raise ValueError(f"Could not parse {path}: {exc}") from exc

    league_name = None
    if parser.has_section(LEAGUE_SECTION):
        raw_name = parser.get(LEAGUE_SECTION, "name", fallback="").strip()
        league_name = raw_name or None

    if not parser.has_section(URLS_SECTION):
        raise ValueError(f"Missing [{URLS_SECTION}] section in {path}")

    urls = []
    seen = set()
    for option, value in parser.items(URLS_SECTION, raw=True):
        if value is None:
            raw_url = option
        elif option.startswith(("http://", "https://")):
            raw_url = f"{option}={value}"
        else:
            raw_url = value
        url = validate_url(raw_url, path)
        if url not in seen:
            urls.append(url)
            seen.add(url)

    return ImportSettings(
        league_name=league_name,
        urls=urls,
        signature=settings_signature(path),
    )


def read_import_settings(path: Path) -> ImportSettings:
    if path.suffix.lower() in {".ini", ".cfg"}:
        return read_ini_settings(path)
    return ImportSettings(league_name=None, urls=read_urls(path), signature=None)


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


def build_payload(
    teams: list[dict],
    league_name: str | None = None,
    settings_path: Path | None = None,
    settings_signature_value: str | None = None,
) -> dict:
    payload = {
        "leagueName": league_name or default_league_name(),
        "teams": teams,
    }
    if settings_path and settings_signature_value:
        payload["source"] = {
            "type": "league.ini",
            "path": str(settings_path.name),
            "settingsSignature": settings_signature_value,
            "importedAt": datetime.now(timezone.utc).isoformat(),
        }
    return payload


def league_cache_needs_refresh(
    settings_path: Path = SETTINGS_PATH,
    league_path: Path = LEAGUE_PATH,
) -> bool:
    if not settings_path.exists():
        return False
    if not league_path.exists():
        return True

    try:
        payload = json.loads(league_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True

    source = payload.get("source") if isinstance(payload, dict) else None
    if not isinstance(source, dict):
        return True

    return source.get("settingsSignature") != settings_signature(settings_path)


def import_league_from_settings(
    settings_path: Path = SETTINGS_PATH,
    league_path: Path = LEAGUE_PATH,
    league_name_override: str | None = None,
) -> dict:
    settings = read_import_settings(settings_path)
    if not settings.urls:
        raise ValueError(f"No URLs found in {settings_path}")

    teams = import_teams(settings.urls)
    payload = build_payload(
        teams,
        league_name_override or settings.league_name,
        settings_path if settings.signature else None,
        settings.signature,
    )
    league_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def ensure_league_cache() -> bool:
    if not SETTINGS_PATH.exists() or not league_cache_needs_refresh():
        return False

    import_league_from_settings()
    print(f"Wrote {LEAGUE_PATH}")
    return True
