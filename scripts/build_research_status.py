#!/usr/bin/env python3
"""Compact fail-closed production readiness snapshot for the mobile homepage."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUTPUT = Path("data/research_status.json")


def checked_age(value, now):
    try:
        checked = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if checked.tzinfo is None:
            return None
        age = (now - checked).total_seconds() / 3600
        return round(age, 1) if age >= 0 else None
    except (ValueError, TypeError):
        return None


def build(history, rosters, matchups, seasons, rolling, now):
    rows = history.get("rows") if isinstance(history.get("rows"), list) else []
    teams = rosters.get("teams") if isinstance(rosters.get("teams"), list) else []
    upcoming = matchups.get("matchups") if isinstance(matchups.get("matchups"), list) else []
    season_coverage = seasons.get("season_coverage") if isinstance(seasons.get("season_coverage"), list) else []
    model_windows = rolling.get("windows") if isinstance(rolling.get("windows"), list) else []
    history_age = checked_age(history.get("checked_at"), now)
    roster_age = checked_age(rosters.get("checked_at"), now)
    blockers = ["independent_game_day_availability_not_verified",
                "injury_clearance_not_verified",
                "sportsbook_line_calibration_not_validated"]
    if history.get("status") != "ok" or not rows:
        blockers.append("historical_box_scores_unavailable")
    if history_age is None or history_age > 72:
        blockers.append("historical_snapshot_stale_or_undated")
    if not teams or not any(t.get("status") == "listed" for t in teams if isinstance(t, dict)):
        blockers.append("roster_identity_snapshot_unavailable")
    if roster_age is None or roster_age > 24:
        blockers.append("roster_snapshot_stale_or_undated")
    if len([s for s in season_coverage if isinstance(s, dict) and s.get("observed_events", 0) >= 8]) < 2:
        blockers.append("two_seasons_with_usable_history_not_confirmed")
    if not any(t.get("status") == "research_only" for t in seasons.get("tests", [])
               if isinstance(t, dict)):
        blockers.append("cross_season_evaluation_insufficient")
    if not model_windows:
        blockers.append("rolling_evaluation_unavailable")
    return {
        "status": "research_only",
        "checked_at": now.isoformat(),
        "prediction_ready": False,
        "history": {"status": history.get("status", "unavailable"),
                    "rows": len(rows), "games": history.get("games", 0),
                    "age_hours": history_age,
                    "archive_2024_status": history.get("archive_2024_status", "not_collected"),
                    "archive_2024_games_added": history.get("archive_2024_games_added", 0),
                    "archive_2025_status": history.get("archive_2025_status", "not_collected"),
                    "archive_2025_games_added": history.get("archive_2025_games_added", 0)},
        "rosters": {"status": rosters.get("status", "unavailable"),
                    "teams_with_listings": sum(t.get("status") == "listed" for t in teams
                                               if isinstance(t, dict)),
                    "age_hours": roster_age},
        "upcoming_matchups": len(upcoming),
        "seasons_observed": [s.get("season") for s in season_coverage if isinstance(s, dict)],
        "season_tests_with_observations": sum(t.get("status") == "research_only"
                                              for t in seasons.get("tests", []) if isinstance(t, dict)),
        "rolling_windows": len(model_windows),
        "readiness_blockers": blockers,
        "limitations": "Data presence, freshness and research evaluations do not establish reliable player availability, calibrated odds or profitable betting recommendations."
    }


def read(name):
    try:
        value = json.loads((Path("data") / (name + ".json")).read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def main():
    now = datetime.now(timezone.utc)
    result = build(*(read(name) for name in
                     ("history", "rosters", "matchups", "opponent_seasons", "opponent_rolling")), now)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("Research readiness:", result["status"], len(result["readiness_blockers"]), "blockers")


if __name__ == "__main__":
    main()
