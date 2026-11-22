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


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    checked = datetime.now(timezone.utc).isoformat()
    try:
        board = fetch(SCOREBOARD)
        completed = [event for event in board.get("events", []) if ((event.get("status") or {}).get("type") or {}).get("state") == "post"]
        rows = []
        for event in completed[:MAX_GAMES]:
            try:
                summary = fetch(SUMMARY + "?" + urlencode({"event": event["id"]}))
                rows.extend(extract(event, summary))
            except Exception:
                continue
        rows = rows[:MAX_PLAYERS]
        result = {"status": "ok" if rows else "no_stats", "checked_at": checked,
                  "source": "ESPN public NFL game box scores", "games_checked": min(len(completed), MAX_GAMES), "players": rows}
    except Exception:
        result = {"status": "fetch_failed", "checked_at": checked, "source": "ESPN public NFL game box scores", "players": []}
    OUTPUT.write_text(json.dumps(result, indent=2))
    print(f"Player box scores: {result['status']}, {len(result['players'])} rows")


if __name__ == "__main__":
    main()
