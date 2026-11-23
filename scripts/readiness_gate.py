#!/usr/bin/env python3
"""Explicit readiness gate: historical samples cannot verify availability.

Do not infer injury clearance or active-roster status from box scores,
historical team names, sportsbook odds, or an upcoming schedule listing.
"""
def evaluate(matchup):
    reasons = []
    if matchup.get("sample_quality") != "sufficient_recent_sample":
        reasons.append("historical_sample_not_sufficient")
    if matchup.get("availability") != "verified_active":
        reasons.append("active_roster_not_verified")
    if matchup.get("injury_status") != "verified_available":
        reasons.append("injury_availability_not_verified")
    if matchup.get("matchup_adjustment") is None:
        reasons.append("opponent_adjustment_unavailable")
    # No trustworthy verified-active/injury feed is integrated yet.
    # Even an upstream record claiming these statuses cannot bypass this gate.
    reasons.append("independent_availability_source_not_integrated")
    return {"prediction_ready": False, "readiness_blockers": reasons,
            "readiness_status": "research_only"}

def annotate(matchups):
    return [{**m, **evaluate(m)} for m in matchups]
