#!/usr/bin/env python3
"""Join player history to upcoming scoreboard matchups without guessing injuries."""
import json
import importlib.util
spec = importlib.util.spec_from_file_location("readiness_gate", "scripts/readiness_gate.py")
readiness_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readiness_gate)
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("data/matchups.json")
def build(games, players, now, rosters=None):
    roster_index = {}
    for team in (rosters or {}).get("teams", []):
        if team.get("status") != "listed":
            continue
        name = team.get("team")
        roster_index[name] = {str(a.get("player_id")) for a in team.get("athletes", [])
                              if a.get("player_id")}
    upcoming = []
    for game in games:
        try:
            start = datetime.fromisoformat(str(game.get("start", "")).replace("Z", "+00:00"))
        except (TypeError, ValueError):
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
        player_id = str(player.get("player_id") or "").strip()
        player_name = str(player.get("player") or "").strip()
        if not team or not player_id or not player_name:
            continue
        for game in upcoming:
            if team not in (game["home"], game["away"]):
                continue
            matches.append({"player": player_name, "player_id": player_id, "team": team,
                            "market": player.get("market"),
                            "games_sampled": player.get("games"),
                            "sample_quality": player.get("sample_quality", "unavailable"),
                            "sample_quality_reasons": player.get("sample_quality_reasons", []),
                            "opponent": game["away"] if team == game["home"] else game["home"],
                            "game_start": game["start"],
                            "roster_listing": ("listed" if player_id in roster_index[team]
                                               else "not_found_in_snapshot") if team in roster_index
                                              else "unavailable",
                            "roster_listing_source": "ESPN team roster snapshot",
                            "availability": "unverified",
                            "injury_status": "unverified",
                            "matchup_adjustment": None,
                            "prediction_ready": False})
    return readiness_gate.annotate(matches)

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        games = json.loads(Path("data/games.json").read_text())
        baseline = json.loads(Path("data/baseline.json").read_text())
        try:
            rosters = json.loads(Path("data/rosters.json").read_text())
        except (OSError, ValueError, TypeError):
            rosters = {}
        matches = build(games.get("games", []) if games.get("status") == "ok" else [],
                        baseline.get("players", []) if baseline.get("status") == "ok" else [],
                        datetime.now(timezone.utc), rosters)
        result = {"status": "ok" if matches else "no_upcoming_player_matchups",
                  "checked_at": datetime.now(timezone.utc).isoformat(), "matchups": matches}
    except (OSError, ValueError, TypeError):
        result = {"status": "unavailable", "matchups": []}
    result["limitations"] = "Opponent pairing and ESPN roster listing cross-check only; roster listing is not active-game status. Injury and active-roster status unverified. No opponent-strength adjustment or player prediction."
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("Upcoming player matchups:", len(result["matchups"]))
if __name__ == "__main__":
    main()
