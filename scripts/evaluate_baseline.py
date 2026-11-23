#!/usr/bin/env python3
"""Evaluate a simple *historical* rushing/receiving yard baseline chronologically.

For each player/market, predict next-game yards using only prior observed games.
Report MAE and count; never present as a validated prop betting probability.
"""
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path

spec_observations = importlib.util.spec_from_file_location("observations", "scripts/observations.py")
observations = importlib.util.module_from_spec(spec_observations)
spec_observations.loader.exec_module(observations)

HISTORY = Path("data/history.json")
OUTPUT = Path("data/evaluation.json")
MIN_TRAIN_GAMES = 2


def parse_yards(row):
    category = str(row.get("category", "")).lower()
    if category not in ("rushing", "receiving"):
        return None
    try:
        yards = float(str((row.get("stats") or {}).get("YDS", "")).replace(",", ""))
    except (ValueError, TypeError):
        return None
    if not math.isfinite(yards):
        return None
    return category, yards


def evaluate(rows):
    by_player = defaultdict(dict)
    for row in observations.unique_rows(rows):
        parsed = parse_yards(row)
        player_id = str(row.get("player_id") or "").strip()
        event_id = str(row.get("event_id") or "").strip()
        date = str(row.get("game_date") or "").strip()
        if not parsed or not player_id or not event_id or not date:
            continue
        category, yards = parsed
        by_player[(player_id, category)][event_id] = (date, yards)
    predictions = []
    for (player_id, category), games in by_player.items():
        # Do not evaluate same-date games against one another.
        ordered = sorted(games.items(), key=lambda kv: (kv[1][0], kv[0]))
        for i in range(MIN_TRAIN_GAMES, len(ordered)):
            date, actual = ordered[i][1]
            prior = [item[1][1] for item in ordered[:i] if item[1][0] < date]
            if len(prior) < MIN_TRAIN_GAMES:
                continue
            estimate = sum(prior) / len(prior)
            recent = sum(prior[-3:]) / len(prior[-3:])
            last_game = prior[-1]
            predictions.append({"category": category, "date": date,
                                "actual": actual, "predicted": round(estimate, 4),
                                "absolute_error": abs(actual - estimate),
                                "recent_three_error": abs(actual - recent),
                                "last_game_error": abs(actual - last_game),
                                "training_games": len(prior)})
    metrics = {}
    for category in ("rushing", "receiving"):
        subset = [p for p in predictions if p["category"] == category]
        metrics[category] = {
            "evaluated_games": len(subset),
            "mae_yards": round(sum(p["absolute_error"] for p in subset) / len(subset), 2) if subset else None,
            "recent_three_mae_yards": round(sum(p["recent_three_error"] for p in subset) / len(subset), 2) if subset else None,
            "last_game_mae_yards": round(sum(p["last_game_error"] for p in subset) / len(subset), 2) if subset else None,
        }
    return {"evaluated_games": len(predictions), "metrics": metrics}


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(HISTORY.read_text())
        result = evaluate(data.get("rows") or []) if data.get("status") == "ok" else evaluate([])
        result.update({"status": "ok" if result["evaluated_games"] else "insufficient_data",
                       "history_checked_at": data.get("checked_at"),
                       "source": "ESPN observed box scores",
                       "method": "Paired chronological evaluation: expanding prior-game mean, last-three mean, and last-game value; 2+ prior games",
                       "limitations": "Tiny, bounded, nonrandom game sample. No opponent or injury adjustment; no calibration, win probability, or betting value."})
    except Exception:
        result = {"status": "unavailable", "evaluated_games": 0, "metrics": {},
                  "limitations": "Evaluation unavailable; no forecast claims."}
    OUTPUT.write_text(json.dumps(result, indent=2))
    print(f"Walk-forward evaluation: {result['status']}; {result['evaluated_games']} observations")


if __name__ == "__main__":
    main()
