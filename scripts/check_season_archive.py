#!/usr/bin/env python3
"""Validate ESPN historical archive coverage before caching or merging.

A cacheable archive is *usable*, not a certified complete NFL season.
Do not persist sparse or contaminated archives across future deployments.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

MIN_CACHE_GAMES = 200
MAX_FAILED_SCOREBOARD_DAYS = 12


def nfl_season(value):
    try:
        day = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return day.year if day.month >= 7 else day.year - 1
    except (TypeError, ValueError):
        return None


def inspect(archive):
    problems = []
    if archive.get("status") != "ok" or archive.get("season") != 2025:
        problems.append("archive unavailable or wrong season label")
    rows = archive.get("rows")
    if not isinstance(rows, list):
        return {"cacheable": False, "safe_to_merge": False,
                "event_count": 0, "rows": 0, "issues": problems + ["invalid rows"]}
    events = set()
    dates = set()
    wrong_season = 0
    invalid = 0
    for row in rows:
        if not isinstance(row, dict) or not str(row.get("event_id") or "").strip():
            invalid += 1
            continue
        season = nfl_season(row.get("game_date"))
        if season != 2025:
            wrong_season += 1
            continue
        events.add(str(row["event_id"]))
        dates.add(str(row["game_date"])[:10])
    if invalid:
        problems.append(f"{invalid} invalid rows")
    if wrong_season:
        problems.append(f"{wrong_season} rows outside 2025 NFL season")
    reported_games = archive.get("games")
    if type(reported_games) is not int or reported_games != len(events):
        problems.append("reported games disagree with unique event IDs")
    safe = not problems and bool(events)
    attempted = archive.get("scoreboard_days_attempted", 0)
    failed = archive.get("scoreboard_days_failed", 0)
    cacheable = (safe and len(events) >= MIN_CACHE_GAMES and len(dates) >= 12
                 and type(attempted) is int and attempted >= 100
                 and type(failed) is int and 0 <= failed <= MAX_FAILED_SCOREBOARD_DAYS)
    if not cacheable:
        problems.append("not enough reliable coverage to cache permanently")
    return {"cacheable": cacheable, "safe_to_merge": safe,
            "event_count": len(events), "rows": len(rows),
            "observed_dates": len(dates), "issues": problems}


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/archive_2025.json")
    try:
        archive = json.loads(path.read_text())
        result = inspect(archive)
    except (OSError, ValueError, TypeError):
        result = {"cacheable": False, "safe_to_merge": False, "event_count": 0,
                  "rows": 0, "issues": ["archive missing or malformed"]}
    print(json.dumps(result))
    if "--cacheable" in sys.argv:
        raise SystemExit(0 if result["cacheable"] else 1)


if __name__ == "__main__":
    main()
