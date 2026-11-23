#!/usr/bin/env python3
"""Collect bounded 2024 NFL season ESPN box scores for cross-season research.

Runs only on cache miss; records actual ESPN coverage, never fills gaps.
"""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location("history", "scripts/fetch_history.py")
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)

OUTPUT = Path("data/archive_2024.json")
ANCHOR = datetime(2025, 2, 11, tzinfo=timezone.utc)
ARCHIVE_WEEKS = 23
ARCHIVE_MAX_GAMES = 320


def collect(fetch):
    old_weeks, old_games = history.WEEKS_BACK, history.MAX_GAMES
    try:
        history.WEEKS_BACK, history.MAX_GAMES = ARCHIVE_WEEKS, ARCHIVE_MAX_GAMES
        diagnostics = {}
        events = history.recent_completed_events(ANCHOR, fetch, diagnostics)
        rows, games = history.assemble(events, fetch, diagnostics)
    finally:
        history.WEEKS_BACK, history.MAX_GAMES = old_weeks, old_games
    return {
        "status": "ok" if rows else "no_history",
        "season": 2024, "games": games, "rows": rows,
        "events_discovered": len(events), **diagnostics,
        "limitations": "Bounded 2024 ESPN NFL game archive. Scoreboard or summary gaps, row caps, and nonrandom collection may limit coverage; not certified complete or betting-ready."
    }


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    try:
        result = collect(history.players.fetch)
    except Exception:
        result = {"status": "fetch_failed", "season": 2024, "games": 0, "rows": []}
    result["checked_at"] = now.isoformat()
    result["source"] = "ESPN public 2024 NFL completed-game box scores"
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("2024 season archive:", result["status"], result["games"], len(result["rows"]))


if __name__ == "__main__":
    main()
