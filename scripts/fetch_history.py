#!/usr/bin/env python3
"""Build a bounded historical NFL player box-score dataset from public ESPN endpoints.

Uses previous completed weeks, avoids current incomplete games, and never fabricates
observations. A single weekly snapshot is not a calibrated predictive model.
"""
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

spec = importlib.util.spec_from_file_location("fetch_players", "scripts/fetch_players.py")
players = importlib.util.module_from_spec(spec)
spec.loader.exec_module(players)

OUTPUT = Path("data/history.json")
WEEKS_BACK = 6
MAX_GAMES = 36
MAX_ROWS = 3000
# NFL regular-season games commonly occur on Thursday, Sunday and Monday.
GAME_WEEKDAYS = (3, 6, 0)


def recent_completed_events(today, fetch):
    found = {}
    # Anchor weeks on the latest *completed* Sunday, rather than the run day.
    # Sampling only the run's weekday previously missed most NFL games.
    sunday = today.date() - timedelta(days=(today.weekday() - 6) % 7)
    if today.weekday() == 6:
        sunday -= timedelta(days=7)  # Today's games may not be completed.
    for weeks_ago in range(WEEKS_BACK):
        week_sunday = sunday - timedelta(weeks=weeks_ago)
        for weekday in GAME_WEEKDAYS:
            offset = (weekday - 6) % 7
            if weekday == 3:
                offset = -3  # Thursday preceding that Sunday
            day = (week_sunday + timedelta(days=offset)).strftime("%Y%m%d")
            url = players.SCOREBOARD + "?" + urlencode({"dates": day, "limit": 100})
            try:
                board = fetch(url)
            except Exception:
                continue
            for event in board.get("events", []):
                if ((event.get("status") or {}).get("type") or {}).get("state") != "post":
                    continue
                event_id = str(event.get("id", ""))
                if event_id:
                    found[event_id] = event
    return sorted(found.values(), key=lambda event: event.get("date", ""), reverse=True)[:MAX_GAMES]


def assemble(events, fetch):
    rows = []
    games = 0
    for event in events:
        try:
            summary = fetch(players.SUMMARY + "?" + urlencode({"event": event["id"]}))
            extracted = players.extract(event, summary)
            if extracted:
                rows.extend(extracted)
                games += 1
        except Exception:
            continue
        if len(rows) >= MAX_ROWS:
            break
    return rows[:MAX_ROWS], games


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    try:
        events = recent_completed_events(now, players.fetch)
        rows, games = assemble(events, players.fetch)
        result = {
            "status": "ok" if rows else "no_history",
            "checked_at": now.isoformat(),
            "source": "ESPN public NFL completed game box scores",
            "games": games,
            "rows": rows,
            "limitations": "Bounded Thursday/Sunday/Monday sampling from six recent completed NFL weeks; excludes unusual game days, not full-season coverage or calibrated predictions."
        }
    except Exception:
        result = {"status": "fetch_failed", "checked_at": now.isoformat(), "source": "ESPN public NFL completed game box scores", "games": 0, "rows": []}
    OUTPUT.write_text(json.dumps(result, indent=2))
    print(f"Historical box scores: {result['status']}; {result['games']} games; {len(result['rows'])} rows")


if __name__ == "__main__":
    main()
