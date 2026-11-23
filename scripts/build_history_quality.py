#!/usr/bin/env python3
"""Describe completeness of collected historical ESPN game summaries.

Counts are diagnostic, not a claim that ESPN provides every NFL game.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("data/history_quality.json")

def build(history):
    rows = history.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    discovered = history.get("events_discovered")
    extracted = history.get("games")
    discovered = discovered if type(discovered) is int and discovered >= 0 else None
    extracted = extracted if type(extracted) is int and extracted >= 0 else None
    ids = {str(r.get("event_id")) for r in rows if isinstance(r, dict) and r.get("event_id")}
    unique_players = {str(r.get("player_id")) for r in rows if isinstance(r, dict) and r.get("player_id")}
    categories = Counter(str(r.get("category") or "unknown") for r in rows if isinstance(r, dict))
    dates = sorted({str(r.get("game_date"))[:10] for r in rows if isinstance(r, dict) and r.get("game_date")})
    missing = max(0, discovered - extracted) if discovered is not None and extracted is not None else None
    coverage = round(extracted / discovered, 4) if discovered and extracted is not None else None
    return {
        "status": "ok" if history.get("status") == "ok" and rows else "insufficient_data",
        "source_status": history.get("status", "unavailable"),
        "history_checked_at": history.get("checked_at"),
        "events_discovered": discovered,
        "games_with_boxscores": extracted,
        "discovered_events_without_usable_boxscores": missing,
        "boxscore_extraction_rate": coverage,
        "unique_events_in_rows": len(ids),
        "unique_players": len(unique_players),
        "stat_rows": len(rows),
        "earliest_game_date": dates[0] if dates else None,
        "latest_game_date": dates[-1] if dates else None,
        "categories": [{"name": k, "rows": v} for k,v in sorted(categories.items())],
        "limitations": "The rate measures usable summaries among ESPN-discovered events, not total NFL schedule coverage. An incomplete scoreboard, missing player rows, skipped fetches, or incomplete game summaries can distort these counts. These are diagnostics, not predictive accuracy."
    }

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        history = json.loads(Path("data/history.json").read_text())
        result = build(history)
    except (OSError, ValueError, TypeError):
        result = build({})
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("History quality:", result["status"], result["stat_rows"], "rows")

if __name__ == "__main__":
    main()
