#!/usr/bin/env python3
"""Collect 2025 NFL season box scores once for a reusable historical archive.

A 23-week Tuesday-to-Monday sampling window centered on Super Bowl LX
includes the 2025 regular season and playoffs, subject to ESPN coverage.
Archive failure does not fabricate results; the current season still works.
"""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location("history", "scripts/fetch_history.py")
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)

OUTPUT = Path("data/archive_2025.json")
ANCHOR = datetime(2026, 2, 10, tzinfo=timezone.utc)
ARCHIVE_WEEKS = 23
ARCHIVE_MAX_GAMES = 320


def collect(fetch):
    original_weeks = history.WEEKS_BACK
    original_games = history.MAX_GAMES
    try:
        history.WEEKS_BACK = ARCHIVE_WEEKS
        history.MAX_GAMES = ARCHIVE_MAX_GAMES
        diagnostics = {}
        events = history.recent_completed_events(ANCHOR, fetch, diagnostics)
        rows, games = history.assemble(events, fetch, diagnostics)
    finally:
        history.WEEKS_BACK = original_weeks
        history.MAX_GAMES = original_games
    return {
        "status": "ok" if rows else "no_history",
        "season": 2025,
        "games": games,
        "rows": rows,
        "events_discovered": len(events),
        **diagnostics,
        "limitations": "Bounded 2025 ESPN public box-score archive. Missing dates, failed requests and row limits may reduce season coverage. Does not prove a complete season or model validity."
    }


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    try:
        result = collect(history.players.fetch)
    except Exception:
        result = {"status": "fetch_failed", "season": 2025, "games": 0, "rows": []}
    result["checked_at"] = now.isoformat()
    result["source"] = "ESPN public 2025 NFL completed-game box scores"
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("2025 season archive:", result["status"], result["games"], len(result["rows"]))


if __name__ == "__main__":
    main()
