#!/usr/bin/env python3
"""Summarize roster snapshot coverage without implying active or injury clearance."""
import json
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("data/roster_quality.json")


def build(rosters, matchups):
    teams = rosters.get("teams", []) if isinstance(rosters.get("teams"), list) else []
    rows = matchups.get("matchups", []) if isinstance(matchups.get("matchups"), list) else []
    valid = [t for t in teams if isinstance(t, dict)]
    statuses = {status: sum(t.get("status") == status for t in valid)
                for status in ("listed", "fetch_failed", "empty_or_unrecognized")}
    player_ids = {str(a.get("player_id")) for t in valid if t.get("status") == "listed"
                  for a in t.get("athletes", []) if isinstance(a, dict) and a.get("player_id")}
    unique = {(str(m.get("player_id")), str(m.get("team")))
              for m in rows if isinstance(m, dict) and m.get("player_id") and m.get("team")}
    listing = {status: sum(m.get("roster_listing") == status for m in rows
                           if isinstance(m, dict))
               for status in ("listed", "not_found_in_snapshot", "unavailable")}
    return {"status": "ok" if valid else "unavailable",
            "roster_checked_at": rosters.get("checked_at"),
            "roster_source_status": rosters.get("status", "unavailable"),
            "teams_requested": len(valid),
            "teams_with_listings": statuses["listed"],
            "teams_fetch_failed": statuses["fetch_failed"],
            "teams_empty_or_unrecognized": statuses["empty_or_unrecognized"],
            "unique_athlete_ids": len(player_ids),
            "upcoming_player_team_pairs": len(unique),
            "upcoming_matchup_rows": len(rows),
            "matchup_listed": listing["listed"],
            "matchup_not_found": listing["not_found_in_snapshot"],
            "matchup_unavailable": listing["unavailable"],
            "prediction_ready": False,
            "limitations": "Team roster IDs and historical player matches are descriptive only. Roster presence does not verify injury clearance, game-day active status or projected usage. Unlisted players are not necessarily inactive. A missing/failed roster is not evidence of a player being out."}


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        rosters = json.loads(Path("data/rosters.json").read_text())
        matchups = json.loads(Path("data/matchups.json").read_text())
        result = build(rosters, matchups)
    except (OSError, ValueError, TypeError):
        result = build({}, {})
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("Roster quality:", result["status"], result["teams_with_listings"])


if __name__ == "__main__":
    main()
