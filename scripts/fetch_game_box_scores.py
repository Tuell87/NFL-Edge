"""Publish box scores for the completed games listed on the Games tab."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode

from fetch_players import SUMMARY, extract, fetch

SCHEDULE = Path("data/games.json")
OUTPUT = Path("data/game_box_scores.json")


def collect_game(game, fetch_summary):
    game_id = str(game["id"])
    summary = fetch_summary(SUMMARY + "?" + urlencode({"event": game_id}))
    event = {
        "id": game_id,
        "date": game.get("start"),
        "name": f"{game['away']['name']} at {game['home']['name']}",
    }
    teams = []
    for team_row in (summary.get("boxscore") or {}).get("teams") or []:
        stats = {
            stat["name"]: {
                "label": stat.get("label") or stat.get("displayName") or stat["name"],
                "value": str(stat["displayValue"]),
            }
            for stat in team_row.get("statistics") or []
            if stat.get("name") and stat.get("displayValue") is not None
        }
        if stats:
            teams.append({
                "name": (team_row.get("team") or {}).get("displayName", ""),
                "stats": stats,
            })
    return {"players": extract(event, summary), "teams": teams}


def collect(schedule, fetch_summary=fetch):
    completed = {
        str(game["id"]): game
        for game in schedule.get("games", [])
        if game.get("state") == "post" and str(game.get("id") or "").isdigit()
    }

    def read(game_id):
        try:
            return game_id, collect_game(completed[game_id], fetch_summary)
        except (OSError, ValueError, KeyError, TypeError):
            return game_id, None

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = dict(pool.map(read, completed))
    games = {key: value for key, value in results.items() if value and (value["players"] or value["teams"])}
    return {"games": games, "games_checked": len(completed)}


def main():
    try:
        schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        schedule = {}
    output = collect(schedule)
    output["checked_at"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, separators=(",", ":")), encoding="utf-8")
    print(f"Finished-game box scores: {len(output['games'])} of {output['games_checked']}")


if __name__ == "__main__":
    main()
