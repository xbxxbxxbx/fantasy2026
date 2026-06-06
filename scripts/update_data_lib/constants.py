from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "docs" / "config.json"
CONFIG_SCRIPT_PATH = ROOT / "docs" / "config.js"
SETTINGS_PATH = ROOT / "league.ini"
SETUP_LOG_PATH = ROOT / "setup.log"
LEAGUE_PATH = ROOT / "league.json"
OUTPUT_PATH = ROOT / "docs" / "data.json"
ACTIVE_OUTPUT_PATH = ROOT / "docs" / "active-players.json"
PLAYER_HISTORY_OUTPUT_PATH = ROOT / "docs" / "25k-player-history.json"
HISTORY_DIR = ROOT / "docs" / "history"
DISPLAY_TIMEZONE = ZoneInfo("America/New_York")
