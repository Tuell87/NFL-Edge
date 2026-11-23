#!/usr/bin/env python3
"""Cross-feed integrity diagnostics for the published NFL Edge data pipeline.

Only malformed identities or impossible counts fail the build. Missing coverage
is reported as a warning because ESPN availability is not guaranteed.
"""
import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUTPUT = Path("data/feed_integrity.json")


def timestamp(value):
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result if result.tzinfo is not None else None
    except (ValueError, TypeError):
        return None


def build(history, games, rosters, matchups, now):
    warnings, errors = [], []
    historical = history.get("rows", []) if isinstance(history.get("rows"), list) else []
    upcoming = matchups.get("matchups", []) if isinstance(matchups.get("matchups"), list) else []
    scheduled = games.get("games", []) if isinstance(games.get("games"), list) else []
    teams = rosters.get("teams", []) if isinstance(rosters.get("teams"), list) else []
    event_ids = set()
    athlete_events = set()
    duplicates = 0
    missing_ids = 0
    for row in historical:
        if not isinstance(row, dict):
            errors.append("history_contains_non_object_row")
            continue
        event, player, category = (str(row.get(k) or "").strip()
                                   for k in ("event_id", "player_id", "category"))
        if not event or not player or not category:
            missing_ids += 1
            continue
        event_ids.add(event)
        key = (event, player, category)
        if key in athlete_events:
            duplicates += 1
        athlete_events.add(key)
    if missing_ids:
        warnings.append("history_rows_missing_stable_identity")
    if duplicates:
        warnings.append("history_duplicate_event_player_category")
    if history.get("status") == "ok" and not historical:
        errors.append("history_ok_but_no_rows")
    reported = history.get("games")
    if type(reported) is int and reported < len(event_ids):
        errors.append("history_game_count_less_than_distinct_events")
    scoreboard_ids = {str(g.get("id")) for g in scheduled
                      if isinstance(g, dict) and g.get("id")}
    unmatched_upcoming = 0
    malformed_matchups = 0
    for row in upcoming:
        if not isinstance(row, dict):
            malformed_matchups += 1
            continue
        if not row.get("player_id") or not row.get("game_start"):
            malformed_matchups += 1
        if row.get("prediction_ready") is not False:
            errors.append("unverified_matchup_prediction_enabled")
    if malformed_matchups:
        warnings.append("matchup_rows_missing_identity_or_start")
    roster_count = sum(1 for t in teams if isinstance(t, dict) and t.get("status") == "listed")
    if not roster_count:
        warnings.append("no_team_roster_listings")
    if history.get("scoreboard_days_failed", 0):
        warnings.append("historical_scoreboard_requests_failed")
    if history.get("row_limit_reached"):
        warnings.append("historical_row_cap_reached")
    if history.get("event_cap_reached"):
        warnings.append("historical_event_cap_reached")
    if not scheduled:
        warnings.append("no_schedule_games")
    checked = timestamp(history.get("checked_at"))
    if not checked or not timedelta(0) <= now - checked <= timedelta(days=3):
        warnings.append("historical_snapshot_missing_or_stale")
    roster_checked = timestamp(rosters.get("checked_at"))
    if not roster_checked or not timedelta(0) <= now - roster_checked <= timedelta(hours=24):
        warnings.append("roster_snapshot_missing_or_stale")
    return {
        "status": "invalid" if errors else "ok",
        "checked_at": now.isoformat(),
        "history_rows": len(historical),
        "history_distinct_events": len(event_ids),
        "history_distinct_event_player_categories": len(athlete_events),
        "history_rows_missing_ids": missing_ids,
        "history_duplicate_keys": duplicates,
        "scheduled_games": len(scheduled),
        "scheduled_game_ids": len(scoreboard_ids),
        "upcoming_matchup_rows": len(upcoming),
        "malformed_matchup_rows": malformed_matchups,
        "roster_teams_with_listings": roster_count,
        "warnings": sorted(set(warnings)),
        "errors": sorted(set(errors)),
        "limitations": "Checks identity, freshness and collector coverage only. No proof of complete NFL schedule, valid injury reports, independent roster clearance, predictive accuracy or betting edge."
    }


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    sources = {}
    for name in ("history", "games", "rosters", "matchups"):
        try:
            sources[name] = json.loads((Path("data") / (name + ".json")).read_text())
        except (OSError, ValueError, TypeError):
            sources[name] = {}
    result = build(*(sources[name] for name in ("history", "games", "rosters", "matchups")), now)
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("Feed integrity:", result["status"], "warnings:", len(result["warnings"]),
          "errors:", len(result["errors"]))


if __name__ == "__main__":
    main()
