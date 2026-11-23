#!/usr/bin/env python3
"""Evaluate a fixed opponent-context method on wholly later NFL seasons.

Training is frozen before each test season: no current-season game is used to
estimate player means, league reference or opponent factors. Incomplete ESPN
history is explicitly marked insufficient and never backfilled with guesses.
"""
import importlib.util
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location("opponent", "scripts/evaluate_opponent.py")
opponent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opponent)

OUTPUT = Path("data/opponent_seasons.json")
MIN_TRAIN_DATES = 8
MIN_TEST_DATES = 4
MIN_TEST_EVENTS = 8


def nfl_season(day):
    """January–June games belong to the preceding NFL season."""
    return day.year if day.month >= 7 else day.year - 1


def evaluate(rows):
    records = opponent.prepare(rows)
    dates_by_season = {}
    events_by_season = {}
    for day, event, player, category, team, opposing_team, yards in records:
        season = nfl_season(day)
        dates_by_season.setdefault(season, set()).add(day)
        events_by_season.setdefault(season, set()).add(event)
    seasons = sorted(dates_by_season)
    result = {
        "status": "insufficient_data", "prediction_ready": False,
        "observed_seasons": seasons, "season_coverage": [
            {"season": season, "observed_dates": len(dates_by_season[season]),
             "observed_events": len(events_by_season[season])}
            for season in seasons],
        "tests": [],
        "method": "Frozen pre-season evaluation. For each later NFL season, player-only and opponent-context yardage means are calculated using exclusively earlier NFL seasons. The fixed opponent method is not retuned on test-season games.",
        "limitations": "NFL seasons assigned by July-to-June calendar. ESPN's rolling 18-week history is not guaranteed to contain multiple complete seasons; partial seasons are not independent validation. No verified game-day roster, injuries, line calibration or betting edge."
    }
    for season in seasons[1:]:
        start, end = date(season, 7, 1), date(season + 1, 7, 1)
        earlier_dates = {d for yr in seasons if yr < season for d in dates_by_season[yr]}
        observed_dates = dates_by_season[season]
        observed_events = events_by_season[season]
        coverage_ok = (len(earlier_dates) >= MIN_TRAIN_DATES
                       and len(observed_dates) >= MIN_TEST_DATES
                       and len(observed_events) >= MIN_TEST_EVENTS)
        if coverage_ok:
            scored = opponent.evaluate(rows, test_start=start, test_end=end, train_end=start)
            metrics = scored["metrics"]
        else:
            metrics = opponent.evaluate([])["metrics"]
        has_pairs = any(m["paired_observations"] for m in metrics)
        result["tests"].append({
            "test_season": season, "training_seasons": [s for s in seasons if s < season],
            "training_dates": len(earlier_dates), "test_dates": len(observed_dates),
            "test_events": len(observed_events),
            "status": "research_only" if coverage_ok and has_pairs else "insufficient_data",
            "metrics": metrics, "prediction_ready": False,
            "coverage_sufficient_for_attempt": coverage_ok
        })
    result["status"] = ("research_only" if any(t["status"] == "research_only" for t in result["tests"])
                        else "insufficient_data")
    return result


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        history = json.loads(Path("data/history.json").read_text())
        result = evaluate(history.get("rows", []) if history.get("status") == "ok" else [])
        result["history_checked_at"] = history.get("checked_at")
    except (OSError, ValueError, TypeError):
        result = evaluate([])
        result["status"] = "unavailable"
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("Season-disjoint opponent validation:", result["status"], len(result["tests"]))


if __name__ == "__main__":
    main()
