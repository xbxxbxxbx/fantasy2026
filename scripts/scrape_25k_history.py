#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from update_data_lib.constants import PLAYER_HISTORY_OUTPUT_PATH
from update_data_lib.player_history import write_player_history


def main() -> int:
    write_player_history()
    print(f"Wrote {PLAYER_HISTORY_OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
