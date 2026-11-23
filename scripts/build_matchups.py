#!/usr/bin/env python3
"""Join player history to upcoming scoreboard matchups without guessing injuries."""
import json
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("data/matchups.json")
def build(games, players, now):
    upcoming = []
    for game in games:
        try:
            start = datetime.fromisoformat(str(game.get("start", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if start.tzinfo is None or start <= now or game.get("state") != "pre":
            continue
        home, away = game.get("home") or {}, game.get("away") or {}
        if not home.get("name") or not away.get("name"):
            continue
        upcoming.append({"id": game.get("id"), "start": game.get("start"),
                         "home": home["name"], "away": away["name"]})
    matches = []
    for player in players:
        team = str(player.get("team") or "").strip()
        if not team:
            continue
        for game in upcoming:
            if team not in (game["home"], game["away"]):
                continue
            matches.append({"player": player.get("player"), "team": team,
                            "market": player.get("market"),
                            "games_sampled": player.get("games"),
                            "opponent": game["away"] if team == game["home"] else game["home"],
                            "game_start": game["start"],
                            "availability": "unverified",
                            "injury_status": "unverified",
                            "matchup_adjustment": None,
                            "prediction_ready": False})
    return matches

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        games = json.loads(Path("data/games.json").read_text())
        baseline = json.loads(Path("data/baseline.json").read_text())
        matches = build(games.get("games", []) if games.get("status") == "ok" else [],
                        baseline.get("players", []) if baseline.get("status") == "ok" else [],
                        datetime.now(timezone.utc))
        result = {"status": "ok" if matches else "no_verified_matchups",
                  "checked_at": datetime.now(timezone.utc).isoformat(), "matchups": matches}
    except (OSError, ValueError, TypeError):
        result = {"status": "unavailable", "matchups": []}
    result["limitations"] = "Opponent pairing only; injury and active-roster status unverified. No opponent-strength adjustment or player prediction."
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("Upcoming player matchups:", len(result["matchups"]))
if __name__ == "__main__":
    main()
