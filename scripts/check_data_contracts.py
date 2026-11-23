#!/usr/bin/env python3
"""Offline CI contract checks for all published NFL Edge JSON outputs."""
import json
import math
from pathlib import Path

DATA = Path("data")
REQUIRED = {
    "odds.json": ("markets",),
    "games.json": ("games",),
    "players.json": ("players",),
    "history.json": ("rows",),
    "baseline.json": ("players",),
    "evaluation.json": ("metrics",),
    "probability_evaluation.json": ("metrics",),
    "matchups.json": ("matchups",),
    "market_audit.json": ("rows",),
    "holdout.json": ("metrics",),
}
LIST_FIELDS = {"markets", "games", "players", "rows", "matchups", "metrics"}
def validate(folder=DATA):
    errors = []
    for filename, fields in REQUIRED.items():
        path = folder / filename
        try:
            with path.open(encoding="utf-8") as f:
                document = json.load(f, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"{filename}: unreadable or invalid JSON ({type(exc).__name__})")
            continue
        if not isinstance(document, dict):
            errors.append(f"{filename}: expected JSON object")
            continue
        if not isinstance(document.get("status"), str):
            errors.append(f"{filename}: missing status string")
        for field in fields:
            if field not in document:
                errors.append(f"{filename}: missing {field}")
            elif field in LIST_FIELDS and not isinstance(document[field], list) and not (
                    filename == "evaluation.json" and field == "metrics" and isinstance(document[field], dict)):
                errors.append(f"{filename}: {field} must be list")
    return errors

if __name__ == "__main__":
    failures = validate()
    for failure in failures:
        print("FAIL:", failure)
    if failures:
        raise SystemExit(1)
    print("PASS: all published JSON files meet the required structural contract")
