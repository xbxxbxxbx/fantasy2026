from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "docs" / "config.json"
LEAGUE_PATH = ROOT / "league.json"
OUTPUT_PATH = ROOT / "docs" / "data.json"
ACTIVE_OUTPUT_PATH = ROOT / "docs" / "active-players.json"
HISTORY_DIR = ROOT / "docs" / "history"
DISPLAY_TIMEZONE = ZoneInfo("America/New_York")
