#!/usr/bin/env python3
"""ESPN roster identity cross-check; roster listing is NOT game-day availability."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

OUTPUT = Path("data/rosters.json")
URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team}/roster"
MAX_TEAMS = 32


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "NFL-Edge/2.0",
                                      "Accept": "application/json"}), timeout=20) as response:
        return json.load(response)


def extract(payload):
    """Extract stable athlete IDs from ESPN's grouped or flat roster structures."""
    athletes = payload.get("athletes")
    if not isinstance(athletes, list):
        return []
    found = {}
    for group in athletes:
        if not isinstance(group, dict):
            continue
        entries = group.get("items") if isinstance(group.get("items"), list) else [group]
        for item in entries:
            if not isinstance(item, dict):
                continue
            athlete_id = str(item.get("id") or "").strip()
            name = str(item.get("displayName") or "").strip()
            if athlete_id and name:
                found[athlete_id] = {"player_id": athlete_id, "player": name}
    return sorted(found.values(), key=lambda a: a["player_id"])


def collect(games, get=fetch):
    teams = {}
    for game in games:
        for side in ("home", "away"):
            team = game.get(side) or {}
            abbr = str(team.get("abbreviation") or "").strip().upper()
            name = str(team.get("name") or "").strip()
            if abbr.isalpha() and 2 <= len(abbr) <= 4 and name:
                teams[abbr] = name
    results = []
    for abbr, name in sorted(teams.items())[:MAX_TEAMS]:
        try:
            roster = extract(get(URL.format(team=abbr.lower())))
            status = "listed" if roster else "empty_or_unrecognized"
        except Exception:
            roster, status = [], "fetch_failed"
        results.append({"team": name, "abbreviation": abbr,
                        "status": status, "athletes": roster})
    return {"status": "ok" if any(t["status"] == "listed" for t in results) else "unavailable",
            "teams": results,
            "teams_requested": len(results),
            "teams_with_rosters": sum(t["status"] == "listed" for t in results),
            "limitations": "ESPN team roster membership is a snapshot, not verification of game-day active status, practice participation, injury clearance or expected playing time. Missing players are not automatically inactive."}


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    try:
        games = json.loads(Path("data/games.json").read_text())
        result = collect(games.get("games", []) if games.get("status") == "ok" else [])
    except (OSError, ValueError, TypeError):
        result = {"status": "unavailable", "teams": [], "teams_requested": 0,
                  "teams_with_rosters": 0, "limitations": "Roster feed unavailable."}
    result["checked_at"] = now
    result["source"] = "ESPN public team roster endpoint"
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("Roster identity cross-check:", result["status"], result["teams_with_rosters"])


if __name__ == "__main__":
    main()
