#!/usr/bin/env python3
"""Describe completeness of collected historical ESPN game summaries.

Counts are diagnostic, not a claim that ESPN provides every NFL game.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("data/history_quality.json")
SPARSE_GAME_PLAYER_THRESHOLD = 10

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
    players_by_event = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        event = str(row.get("event_id") or "").strip()
        player = str(row.get("player_id") or "").strip()
        if event and player:
            players_by_event.setdefault(event, set()).add(player)
    counts = sorted(len(players) for players in players_by_event.values())
    sparse = sum(count < SPARSE_GAME_PLAYER_THRESHOLD for count in counts)
    median = (counts[(len(counts)-1)//2] + counts[len(counts)//2]) / 2 if counts else None
    missing = max(0, discovered - extracted) if discovered is not None and extracted is not None else None
    coverage = round(extracted / discovered, 4) if discovered and extracted is not None else None
    return {
        "status": "ok" if history.get("status") == "ok" and rows else "insufficient_data",
        "source_status": history.get("status", "unavailable"),
        "history_checked_at": history.get("checked_at"),
        "events_discovered": discovered,
        "games_with_boxscores": extracted,
        "scoreboard_days_attempted": history.get("scoreboard_days_attempted"),
        "scoreboard_days_failed": history.get("scoreboard_days_failed"),
        "events_discovered_before_cap": history.get("events_discovered_before_cap"),
        "event_cap_reached": history.get("event_cap_reached"),
        "summaries_attempted": history.get("summaries_attempted"),
        "summaries_without_usable_rows": history.get("summaries_without_usable_rows"),
        "events_not_attempted": history.get("events_not_attempted"),
        "row_limit_reached": history.get("row_limit_reached"),
        "discovered_events_without_usable_boxscores": missing,
        "boxscore_extraction_rate": coverage,
        "unique_events_in_rows": len(ids),
        "unique_players": len(unique_players),
        "games_with_player_ids": len(counts),
        "min_unique_players_per_game": counts[0] if counts else None,
        "median_unique_players_per_game": median,
        "max_unique_players_per_game": counts[-1] if counts else None,
        "sparse_games_under_ten_players": sparse,
        "sparse_game_threshold": SPARSE_GAME_PLAYER_THRESHOLD,
        "stat_rows": len(rows),
        "earliest_game_date": dates[0] if dates else None,
        "latest_game_date": dates[-1] if dates else None,
        "categories": [{"name": k, "rows": v} for k,v in sorted(categories.items())],
        "limitations": "The rate measures usable summaries among ESPN-discovered events, not total NFL schedule coverage. Discovered-minus-extracted includes skipped, failed, and unattempted summaries; it is not strictly a count of missing box scores. Failed scoreboard dates, an incomplete scoreboard, missing player rows, skipped fetches, row caps, or incomplete game summaries can distort these counts. Games with fewer than ten distinct player IDs are flagged for review, not proven incomplete; this heuristic depends on the extracted categories. These are diagnostics, not predictive accuracy."
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
