#!/usr/bin/env python3
"""Fetch a public ESPN NFL scoreboard snapshot; no credential required."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
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


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "NFL-Edge/2.0", "Accept": "application/json"}), timeout=20) as response:
        return json.load(response)


def next_schedule_url(payload):
    season = payload.get("season") or {}
    year = season.get("year")
    leagues = payload.get("leagues") or []
    if type(year) is not int or not leagues:
        return None
    current = (str(season.get("type")), str((payload.get("week") or {}).get("number")))
    calendar = [(str(phase["value"]), str(week["value"]))
                for phase in leagues[0].get("calendar") or [] if "value" in phase
                for week in phase.get("entries") or [] if "value" in week]
    for previous, following in zip(calendar, calendar[1:]):
        if previous == current:
            phase, week = following
            return URL + "?" + urlencode({"dates": year, "seasontype": phase, "week": week})
    return None


def collect(get=fetch):
    payload = get(URL)
    current = normalize(payload)
    next_url = next_schedule_url(payload)
    upcoming = []
    coverage = "current_week_only"
    if next_url:
        try:
            upcoming = [game for game in normalize(get(next_url))
                        if game["state"] == "pre" and game["id"]]
            if upcoming:
                coverage = "next_week_included"
        except (OSError, ValueError):
            coverage = "next_week_unavailable"
    seen = {game["id"] for game in current}
    for game in upcoming:
        if game["id"] not in seen:
            current.append(game)
            seen.add(game["id"])
    return current, coverage


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    checked = datetime.now(timezone.utc).isoformat()
    try:
        games, coverage = collect()
        result = {"status": "ok" if games else "no_games", "checked_at": checked,
                  "source": "ESPN public scoreboard", "games": games, "schedule_coverage": coverage}
    except Exception:
        result = {"status": "fetch_failed", "checked_at": checked, "source": "ESPN public scoreboard", "games": []}
    OUTPUT.write_text(json.dumps(result, indent=2))
    print(f"NFL scoreboard: {result['status']}, {len(result['games'])} games")


if __name__ == "__main__":
    main()
