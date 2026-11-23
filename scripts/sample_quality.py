#!/usr/bin/env python3
"""Conservative descriptive sample-quality flags, NOT prediction confidence."""
from datetime import datetime, timezone

MIN_GAMES = 5
MAX_DAYS_SINCE_GAME = 21

def assess(player, now):
    games = player.get("games")
    games = games if type(games) is int and games >= 0 else 0
    try:
        date = datetime.fromisoformat(str(player.get("last_game_date") or "").replace("Z","+00:00"))
        if date.tzinfo is None:
            raise ValueError("timezone missing")
        age = (now - date).total_seconds() / 86400
    except (TypeError, ValueError, OverflowError):
        age = None
    reasons = []
    if games < MIN_GAMES:
        reasons.append("fewer_than_five_games")
    if age is None or age < 0 or age > MAX_DAYS_SINCE_GAME:
        reasons.append("missing_future_or_stale_game_date")
    return {"sample_quality": "sufficient_recent_sample" if not reasons else "limited_sample",
            "sample_quality_reasons": reasons,
            "days_since_last_game": round(age, 1) if age is not None and age >= 0 else None,
            "prediction_ready": False,
            "note": "Sample-quality screening only. Does not verify roster, injury status, model calibration, or positive expected value."}

def annotate(players, now=None):
    now = now or datetime.now(timezone.utc)
    return [{**p, **assess(p,now)} for p in players]
