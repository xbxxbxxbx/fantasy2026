from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "docs" / "config.json"
SETTINGS_PATH = ROOT / "league.ini"
LEAGUE_PATH = ROOT / "league.json"
OUTPUT_PATH = ROOT / "docs" / "data.json"
ACTIVE_OUTPUT_PATH = ROOT / "docs" / "active-players.json"
PLAYER_HISTORY_OUTPUT_PATH = ROOT / "docs" / "25k-player-history.json"
HISTORY_DIR = ROOT / "docs" / "history"
DISPLAY_TIMEZONE = ZoneInfo("America/New_York")
