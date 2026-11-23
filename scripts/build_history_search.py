#!/usr/bin/env python3
"""Compact, bounded per-player search data for mobile historical box-score UI.

Full history remains available for server-side evaluations and optional exports.
The browser only needs a few recent game rows per player/category, not every
historical ESPN stat in all seasons.
"""
import importlib.util
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

spec_observations = importlib.util.spec_from_file_location("observations", "scripts/observations.py")
observations = importlib.util.module_from_spec(spec_observations)
spec_observations.loader.exec_module(observations)

OUTPUT = Path("data/history_search.json")
RECENT_PER_PLAYER_CATEGORY = 8


def build(history):
    rows = history.get("rows") if isinstance(history.get("rows"), list) else []
    grouped = defaultdict(dict)
    for row in observations.unique_rows(rows):
        if not isinstance(row, dict):
            continue
        player = str(row.get("player_id") or "").strip()
        event = str(row.get("event_id") or "").strip()
        category = str(row.get("category") or "").strip()
        date = str(row.get("game_date") or "").strip()
        if not player or not event or not category or not date:
            continue
        key = (player, category)
        item = {
            "player_id": player, "event_id": event,
            "player": str(row.get("player") or ""),
            "team": str(row.get("team") or ""),
            "category": category, "game_date": date,
            "stats": row.get("stats") if isinstance(row.get("stats"), dict) else {}
        }
        prior = grouped[key].get(event)
        if prior is None or item["game_date"] > prior["game_date"]:
            grouped[key][event] = item
    latest = []
    for group in grouped.values():
        latest.extend(sorted(group.values(), key=lambda r: (r["game_date"], r["event_id"]),
                             reverse=True)[:RECENT_PER_PLAYER_CATEGORY])
    latest.sort(key=lambda r: r["game_date"], reverse=True)
    latest.sort(key=lambda r: (r["player"].casefold(), r["category"]))
    return {
        "status": "ok" if latest and history.get("status") == "ok" else "insufficient_data",
        "checked_at": history.get("checked_at"),
        "source": "Compact subset of ESPN historical box scores",
        "total_history_rows": len(rows),
        "searchable_rows": len(latest),
        "games": history.get("games", 0),
        "recent_games_per_player_category": RECENT_PER_PLAYER_CATEGORY,
        "rows": latest,
        "limitations": "Search contains at most eight latest observed games per player/category, not full historical results, all games, current roster, or predictive recommendations."
    }


def main():
    try:
        source = json.loads(Path("data/history.json").read_text())
        result = build(source if isinstance(source, dict) else {})
    except (OSError, ValueError, TypeError):
        result = build({})
        result["status"] = "unavailable"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, separators=(",", ":"), ensure_ascii=False))
    print("Mobile history search:", result["status"], result["searchable_rows"],
          "of", result["total_history_rows"], "historical rows")


if __name__ == "__main__":
    main()
