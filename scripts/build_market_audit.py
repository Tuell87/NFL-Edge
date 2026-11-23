#!/usr/bin/env python3
"""Audit historical over estimates against actual upcoming FanDuel yardage lines.

Educational estimates are withheld as recommendations when injury and active
status are unverified. Never compute a parlay or suggest positive EV from these.
"""
import importlib.util
import json
import math
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location("prob", "scripts/evaluate_probabilities.py")
prob = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prob)

OUTPUT = Path("data/market_audit.json")
MARKETS = {"player_rush_yds": "rushing", "player_reception_yds": "receiving"}
MAX_AGE = timedelta(hours=24)

def parse_time(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else None
    except (TypeError, ValueError):
        return None

def norm(value):
    return " ".join(str(value or "").casefold().split())

def build(history, odds, matchups, now):
    checked = parse_time(odds.get("updated_at"))
    if odds.get("status") != "ok" or not checked or not timedelta(0) <= now - checked <= MAX_AGE:
        return {"status": "stale_or_missing_odds", "rows": []}
    history_checked = parse_time(history.get("checked_at"))
    if history.get("status") != "ok" or not history_checked or not timedelta(0) <= now - history_checked <= timedelta(days=3):
        return {"status": "stale_or_missing_history", "rows": []}
    groups = defaultdict(dict)
    for row in history.get("rows", []):
        parsed = prob.parse_yards(row)
        if not parsed or not row.get("event_id") or not row.get("game_date"):
            continue
        category, yards = parsed
        name = norm(row.get("player"))
        if not name:
            continue
        groups[(name, category)][str(row["event_id"])] = (str(row["game_date"]), yards)
    matchup_keys = {(norm(m.get("player")), m.get("market"), parse_time(m.get("game_start"))):
                    m for m in matchups if m.get("opponent")}
    candidates = defaultdict(list)
    for item in odds.get("markets", []):
        category = MARKETS.get(item.get("market"))
        line = item.get("line")
        kickoff = parse_time(item.get("commence_time"))
        updated = parse_time(item.get("bookmaker_updated"))
        if (not category or item.get("side") != "Over" or type(line) not in (int, float)
            or not math.isfinite(line) or not kickoff or kickoff <= now
            or not updated or not timedelta(0) <= now - updated <= MAX_AGE
            or type(item.get("odds")) not in (int, float)
            or not math.isfinite(item["odds"]) or item["odds"] == 0):
            continue
        key = (norm(item.get("player")), item["market"], kickoff)
        candidates[key].append(item)
    output = []
    for key, selections in candidates.items():
        if len(selections) != 1 or key not in matchup_keys:
            continue
        selection = selections[0]
        category = MARKETS[selection["market"]]
        previous = [yards for date, yards in groups.get((key[0], category), {}).values()
                    if parse_time(date) and parse_time(date) < parse_time(selection["commence_time"])]
        estimate = prob.estimate(previous, selection["line"])
        if estimate is None:
            continue
        matchup = matchup_keys[key]
        output.append({"player": selection["player"], "market": selection["market"],
                       "line": selection["line"], "odds": selection["odds"],
                       "game_start": selection["commence_time"],
                       "opponent": matchup["opponent"], "prior_games": len(previous),
                       "experimental_over_probability": round(estimate, 4),
                       "injury_status": "unverified", "active_roster": "unverified",
                       "prediction_ready": False, "recommended": False})
    output.sort(key=lambda r: (r["game_start"], r["player"], r["market"]))
    return {"status": "ok" if output else "no_eligible_market_matches", "rows": output}

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    try:
        history = json.loads(Path("data/history.json").read_text())
        odds = json.loads(Path("data/odds.json").read_text())
        matchups = json.loads(Path("data/matchups.json").read_text())
        result = build(history, odds, matchups.get("matchups", []), now)
    except (OSError, ValueError, TypeError):
        result = {"status": "unavailable", "rows": []}
    result["checked_at"] = now.isoformat()
    result["limitations"] = "Uncalibrated historical frequency estimate, not a pick or expected value. Injury/active status and opponent adjustments unverified. No parlays."
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("Market-line audit:", result["status"], len(result["rows"]))

if __name__ == "__main__":
    main()
