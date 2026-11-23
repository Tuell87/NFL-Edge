#!/usr/bin/env python3
"""Separate later-date holdout for the fixed opponent-adjustment experiment.

Scores only the last quarter of observed dates. All features at each target
date use strictly earlier box-score observations. This is retrospective and
not an untouched prospective or season-independent validation.
"""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location("opponent", "scripts/evaluate_opponent.py")
opponent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opponent)

OUTPUT = Path("data/opponent_holdout.json")
MIN_DATES = 8
HOLDOUT_FRACTION = 0.25


def evaluate(rows):
    records = opponent.prepare(rows)
    dates = sorted({record[0] for record in records})
    if len(dates) < MIN_DATES:
        result = opponent.evaluate([], test_start=None)
        result.update({"status": "insufficient_data", "holdout_start": None,
                       "holdout_dates": 0, "observed_dates": len(dates),
                       "evidence_status": "insufficient_holdout_evidence"})
        return result
    cut = max(1, int(len(dates) * (1 - HOLDOUT_FRACTION)))
    cut = min(cut, len(dates) - 1)
    start = dates[cut]
    result = opponent.evaluate(rows, test_start=start)
    result["holdout_start"] = start.isoformat()
    result["holdout_dates"] = len(dates) - cut
    result["observed_dates"] = len(dates)
    result["evidence_status"] = ("preliminary" if all(
        m["evidence_status"] == "preliminary" for m in result["metrics"])
        and result["status"] == "ok" and result["holdout_dates"] >= 4
        else "insufficient_holdout_evidence")
    result["method"] = (
        "Final 25% of observed dates held out for scoring. Fixed player-only "
        "versus opponent-context paired MAE; each forecast uses only earlier "
        "dates. No opponent factor or threshold fitted on held-out outcomes.")
    result["limitations"] = (
        "Retrospective, bounded and possibly incomplete ESPN sample; dates "
        "are not an untouched future trial. Adjustment parameters were "
        "chosen during research, not established by nested model selection. "
        "Correlated observations, roster and injury uncertainty, missing "
        "schedule, season shifts and sportsbook odds prevent betting-edge "
        "claims. Event-cluster intervals are descriptive. Prediction ready: no.")
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
    print("Opponent holdout:", result["status"], result["holdout_start"])


if __name__ == "__main__":
    main()
