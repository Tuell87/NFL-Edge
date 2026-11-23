#!/usr/bin/env python3
"""Collect recent NFL box-score player statistics from ESPN public summaries.

These are observed game results, not forecasts. Fail closed if data unavailable.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
OUTPUT = Path("data/players.json")
MAX_GAMES = 4
MAX_PLAYERS = 200


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "NFL-Edge/2.0", "Accept": "application/json"}), timeout=20) as response:
        return json.load(response)


def extract(event, summary):
    rows = []
    boxscore = summary.get("boxscore") or {}
    for team_group in boxscore.get("players") or []:
        team = (team_group.get("team") or {}).get("displayName", "")
        for category in team_group.get("statistics") or []:
            labels = category.get("labels") or []
            name = category.get("name", "")
            for athlete_row in category.get("athletes") or []:
                athlete = athlete_row.get("athlete") or {}
                values = athlete_row.get("stats") or []
                if not athlete.get("displayName") or not isinstance(values, list):
                    continue
                stats = {str(label): str(value) for label, value in zip(labels, values)}
                if not stats:
                    continue
                rows.append({
                    "event_id": str(event.get("id", "")),
                    "game": event.get("name", ""),
                    "game_date": event.get("date"),
                    "team": team,
                    "player_id": str(athlete.get("id", "")),
                    "player": athlete.get("displayName"),
                    "category": name,
                    "stats": stats,
                })
    return rows


def collect(board, fetch_summary, now):
    """Collect complete recent finished-game box scores without partial-game slicing."""
    events = []
    for event in board.get("events", []):
        if ((event.get("status") or {}).get("type") or {}).get("state") != "post":
            continue
        try:
            start = datetime.fromisoformat(str(event.get("date") or "").replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if start.tzinfo is None or start >= now or not str(event.get("id") or "").strip():
            continue
        events.append(event)
    unique = {str(event["id"]): event for event in events}
    completed = sorted(unique.values(), key=lambda e: e["date"], reverse=True)
    rows = []
    games = 0
    attempts = 0
    failures = 0
    limit_reached = False
    for event in completed:
        if games >= MAX_GAMES:
            break
        attempts += 1
        try:
            extracted = extract(event, fetch_summary(SUMMARY + "?" + urlencode({"event": event["id"]})))
        except Exception:
            failures += 1
            continue
        if not extracted:
            failures += 1
            continue
        if len(rows) + len(extracted) > MAX_PLAYERS:
            limit_reached = True
            break
        rows.extend(extracted)
        games += 1
    return {"status": "ok" if rows else "no_stats",
            "games_checked": attempts, "games_with_stats": games,
            "summary_failures_or_empty": failures,
            "completed_events_discovered": len(completed),
            "events_not_attempted": len(completed) - attempts,
            "player_row_limit_reached": limit_reached,
            "players": rows}


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    checked = datetime.now(timezone.utc)
    try:
        board = fetch(SCOREBOARD)
        result = collect(board, fetch, checked)
    except Exception:
        result = {"status": "fetch_failed", "players": [], "games_checked": 0,
                  "games_with_stats": 0, "summary_failures_or_empty": 0,
                  "completed_events_discovered": 0, "events_not_attempted": 0,
                  "player_row_limit_reached": False}
    result["checked_at"] = checked.isoformat()
    result["source"] = "ESPN public NFL game box scores"
    result["limitations"] = "Bounded most-recent completed-game snapshot, not full roster or injury verification. Empty or failed summaries and row limits can reduce coverage."
    OUTPUT.write_text(json.dumps(result, indent=2))
    print(f"Player box scores: {result['status']}, {len(result['players'])} rows")


if __name__ == "__main__":
    main()
