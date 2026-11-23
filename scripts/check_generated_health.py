#!/usr/bin/env python3
"""Post-build static artifact checks; report unavailable feeds without inventing data."""
import json
import sys
from pathlib import Path

REQUIRED = {
    "rosters.json": ("teams",),
    "roster_quality.json": ("teams_requested", "teams_with_listings", "prediction_ready"),
    "feed_integrity.json": ("warnings", "errors"),
    "matchups.json": ("matchups",),
    "history.json": ("rows",),
    "history_quality.json": ("categories",),
    "holdout.json": ("metrics",),
    "opponent_evaluation.json": ("metrics",),
    "opponent_holdout.json": ("metrics",),
    "opponent_rolling.json": ("windows", "prediction_ready"),
    "market_audit.json": ("rows",),
}


def validate(folder=Path("data")):
    failures = []
    warnings = []
    documents = {}
    for filename, fields in REQUIRED.items():
        try:
            data = json.loads((folder / filename).read_text())
        except (OSError, ValueError, TypeError) as exc:
            failures.append(f"{filename}: missing or invalid ({type(exc).__name__})")
            continue
        if not isinstance(data, dict):
            failures.append(f"{filename}: expected JSON object")
            continue
        documents[filename] = data
        for field in fields:
            if field not in data:
                failures.append(f"{filename}: missing {field}")
        if data.get("status") != "ok":
            warnings.append(f"{filename}: status={data.get('status', 'missing')}")
    integrity = documents.get("feed_integrity.json", {})
    if integrity.get("status") == "invalid" or integrity.get("errors"):
        failures.append("feed_integrity.json: cross-feed integrity errors")
    if isinstance(integrity.get("warnings"), list):
        warnings.extend("feed integrity: " + str(w) for w in integrity["warnings"])
    quality = documents.get("roster_quality.json", {})
    if quality.get("prediction_ready") is not False:
        failures.append("roster_quality.json: must not mark roster data prediction-ready")
    rosters = documents.get("rosters.json", {})
    if rosters.get("teams_with_rosters", 0) == 0:
        warnings.append("ESPN roster coverage unavailable; do not infer player inactivity")
    for filename, field in (("matchups.json", "matchups"), ("market_audit.json", "rows")):
        for row in documents.get(filename, {}).get(field, []):
            if not isinstance(row, dict):
                failures.append(f"{filename}: invalid row")
                continue
            if row.get("prediction_ready") is not False:
                failures.append(f"{filename}: prediction readiness must remain false")
            if filename == "market_audit.json" and row.get("recommended") is not False:
                failures.append(f"{filename}: unverified market row cannot be recommended")
    return failures, warnings


def main():
    errors, warnings = validate()
    for warning in warnings:
        print("WARNING:", warning)
    for error in errors:
        print("ERROR:", error)
    if errors:
        sys.exit(1)
    print("PASS: generated data health and fail-closed prediction checks")


if __name__ == "__main__":
    main()
