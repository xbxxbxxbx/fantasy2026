from __future__ import annotations

import json
import sys

from .config import load_config, write_config_script
from .constants import ACTIVE_OUTPUT_PATH, OUTPUT_PATH
from .league_import import ensure_league_cache
from .player_history import ensure_player_history
from .snapshot import build_snapshot, fetch_active_players_snapshot


def main() -> int:
    try:
        ensure_league_cache()
        ensure_player_history()
        config = load_config()
        write_config_script(config)
        snapshot = build_snapshot(config)
        has_configured_teams = snapshot.get("configuredTeamCount", 0) > 0
        score_snapshot_updated = snapshot.get("successCount", 0) > 0 or not has_configured_teams
        if score_snapshot_updated:
            snapshot.pop("successCount", None)
            snapshot.pop("configuredTeamCount", None)
            OUTPUT_PATH.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        else:
            print(
                "Warning: all team scrapes failed; preserving previous data.json.",
                file=sys.stderr,
            )

        try:
            active_snapshot = fetch_active_players_snapshot()
            ACTIVE_OUTPUT_PATH.write_text(
                json.dumps(active_snapshot, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception as exc:
            print(f"Warning: failed to update active players snapshot: {exc}", file=sys.stderr)
    except Exception as exc:
        print(f"Failed to update data: {exc}", file=sys.stderr)
        return 1

    if score_snapshot_updated:
        print(f"Wrote {OUTPUT_PATH}")
    else:
        print(f"Preserved {OUTPUT_PATH}")
    if ACTIVE_OUTPUT_PATH.exists():
        print(f"Wrote {ACTIVE_OUTPUT_PATH}")
    return 0
