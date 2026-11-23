#!/usr/bin/env python3
"""Experimental walk-forward empirical yardage exceedance calibration.

Only uses earlier observed games for each player. This is not a trained
sportsbook edge model. Missing availability/opponent context is not inferred.
"""
import json
import math
from collections import defaultdict
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location('evaluate_baseline', 'scripts/evaluate_baseline.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
parse_yards = module.parse_yards

HISTORY = Path("data/history.json")
OUTPUT = Path("data/probability_evaluation.json")
THRESHOLDS = (24.5, 49.5, 74.5, 99.5)
MIN_PRIOR = 5
PRIOR_STRENGTH = 4

def brier(probability, outcome):
    return (probability - outcome) ** 2

def estimate(previous, threshold):
    """Laplace/Beta(2,2) smoothing, not market-calibrated."""
    if len(previous) < MIN_PRIOR:
        return None
    wins = sum(yards > threshold for yards in previous)
    return (wins + PRIOR_STRENGTH / 2) / (len(previous) + PRIOR_STRENGTH)

def evaluate(rows):
    grouped = defaultdict(dict)
    for row in rows:
        parsed = parse_yards(row)
        player = str(row.get("player_id") or "").strip()
        event = str(row.get("event_id") or "").strip()
        date = str(row.get("game_date") or "").strip()
        if not parsed or not player or not event or not date:
            continue
        category, yards = parsed
        grouped[(player, category)][event] = (date, yards)
    scores = defaultdict(list)
    for (_, category), games in grouped.items():
        ordered = sorted(games.values(), key=lambda item: item[0])
        for date, actual in ordered:
            prior = [yards for old_date, yards in ordered if old_date < date]
            if len(prior) < MIN_PRIOR:
                continue
            for threshold in THRESHOLDS:
                p = estimate(prior, threshold)
                if p is None:
                    continue
                actual_over = int(actual > threshold)
                scores[(category, threshold)].append((p, actual_over))
    metrics = []
    for (category, threshold), pairs in sorted(scores.items()):
        count = len(pairs)
        mean_p = sum(p for p, _ in pairs) / count
        actual_rate = sum(outcome for _, outcome in pairs) / count
        metrics.append({"category": category, "line": threshold,
                        "evaluated_games": count,
                        "brier": round(sum(brier(p, o) for p, o in pairs) / count, 4),
                        "baseline_brier": round(sum(brier(.5, o) for _, o in pairs) / count, 4),
                        "mean_probability": round(mean_p, 4),
                        "observed_over_rate": round(actual_rate, 4)})
    return {"status": "ok" if metrics else "insufficient_data",
            "evaluated_predictions": sum(x["evaluated_games"] for x in metrics),
            "metrics": metrics}

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        source = json.loads(HISTORY.read_text())
        result = evaluate(source.get("rows", []) if source.get("status") == "ok" else [])
        result["history_checked_at"] = source.get("checked_at")
    except (OSError, ValueError, TypeError):
        result = {"status": "unavailable", "evaluated_predictions": 0, "metrics": []}
    result["method"] = "Prior-player-game empirical over rate, Beta(2,2) smoothed, minimum five prior games"
    result["limitations"] = "Exploratory historical evaluation only; no opponent, injury, availability or schedule adjustment. Brier is evaluated on a limited sample and not proof of betting profitability. Thresholds are illustrative, not sportsbook lines."
    OUTPUT.write_text(json.dumps(result, indent=2))
    print("Probability evaluation:", result["status"], result["evaluated_predictions"])

if __name__ == "__main__":
    main()
