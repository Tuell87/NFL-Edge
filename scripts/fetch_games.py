#!/usr/bin/env python3
"""Fetch a public ESPN NFL scoreboard snapshot; no credential required."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
OUTPUT = Path("data/games.json")


def normalize(payload):
    games = []
    for event in payload.get("events", []):
        competition = (event.get("competitions") or [{}])[0]
        competitors = competition.get("competitors") or []
        teams = {}
        for entry in competitors:
            side = entry.get("homeAway")
            if side not in ("home", "away"):
                continue
            team = entry.get("team") or {}
            teams[side] = {
                "name": team.get("displayName", ""),
                "abbreviation": team.get("abbreviation", ""),
                "score": entry.get("score"),
            }
        if "home" not in teams or "away" not in teams:
            continue
        status = event.get("status") or {}
        status_type = status.get("type") or {}
        games.append({
            "id": str(event.get("id", "")),
            "start": event.get("date"),
            "home": teams["home"],
            "away": teams["away"],
            "status": status_type.get("description", "Unknown"),
            "state": status_type.get("state", ""),
        })
    return games


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    checked = datetime.now(timezone.utc).isoformat()
    try:
        with urlopen(Request(URL, headers={"User-Agent": "NFL-Edge/2.0", "Accept": "application/json"}), timeout=20) as response:
            data = json.load(response)
        games = normalize(data)
        result = {"status": "ok" if games else "no_games", "checked_at": checked, "source": "ESPN public scoreboard", "games": games}
    except Exception:
        result = {"status": "fetch_failed", "checked_at": checked, "source": "ESPN public scoreboard", "games": []}
    OUTPUT.write_text(json.dumps(result, indent=2))
    print(f"NFL scoreboard: {result['status']}, {len(result['games'])} games")


if __name__ == "__main__":
    main()
