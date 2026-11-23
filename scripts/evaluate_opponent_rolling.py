#!/usr/bin/env python3
"""Fixed chronological rolling-origin checks for opponent-context yardage models.

Three non-overlapping later-date scoring windows; earlier dates may train
subsequent windows, but no same-date or future outcomes enter any prediction.
These windows are NOT independent seasons or a prospective trial.
"""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location("opponent", "scripts/evaluate_opponent.py")
opponent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opponent)

OUTPUT = Path("data/opponent_rolling.json")
MIN_DATES = 12
WINDOW_COUNT = 3


def evaluate(rows):
    dates = sorted({r[0] for r in opponent.prepare(rows)})
    output = {
        "status": "insufficient_data", "prediction_ready": False,
        "observed_dates": len(dates), "windows": [],
        "method": "Fixed rolling-origin validation: first quarter of observed dates is warm-up; remaining dates are split into three non-overlapping chronological windows. At each scored game, both methods use only strictly earlier dates. No hyperparameter tuning.",
        "limitations": "Retrospective, possibly incomplete ESPN sample. Windows reuse training history and may share players and seasons; not independent tests. Opponent context is not a verified defensive rating. Event-cluster uncertainty is descriptive; injuries, roster availability, opponent selection, and betting edges remain unverified."
    }
    if len(dates) < MIN_DATES:
        return output
    warmup = len(dates) // 4
    remaining = len(dates) - warmup
    boundaries = [warmup + (remaining * i) // WINDOW_COUNT for i in range(WINDOW_COUNT + 1)]
    for i in range(WINDOW_COUNT):
        start_idx, end_idx = boundaries[i:i + 2]
        if end_idx <= start_idx:
            continue
        start = dates[start_idx]
        end = dates[end_idx] if end_idx < len(dates) else None
        evaluated = opponent.evaluate(rows, test_start=start, test_end=end)
        output["windows"].append({
            "number": i + 1,
            "start": start.isoformat(),
            "end_exclusive": end.isoformat() if end else None,
            "observed_test_dates": end_idx - start_idx,
            "status": evaluated["status"],
            "metrics": evaluated["metrics"],
        })
    summary = []
    for category in ("rushing", "receiving"):
        rows_for_category = [next(m for m in w["metrics"] if m["category"] == category)
                             for w in output["windows"]]
        populated = [m for m in rows_for_category if m["paired_observations"]]
        n = sum(m["paired_observations"] for m in populated)
        player_error = sum(m["paired_observations"] * m["player_only_mae"]
                           for m in populated)
        adjusted_error = sum(m["paired_observations"] * m["opponent_adjusted_mae"]
                             for m in populated)
        improving = sum(m["mae_improvement_yards"] > 0 for m in populated)
        worsening = sum(m["mae_improvement_yards"] < 0 for m in populated)
        summary.append({
            "category": category, "paired_observations": n,
            "windows_with_observations": len(populated),
            "windows_improved": improving,
            "windows_worsened": worsening,
            "pooled_player_only_mae": round(player_error / n, 4) if n else None,
            "pooled_adjusted_mae": round(adjusted_error / n, 4) if n else None,
            "pooled_improvement_yards": round((player_error - adjusted_error) / n, 4) if n else None,
            "evidence_status": "preliminary" if len(populated) == WINDOW_COUNT
                               and n >= 100 and all(m["distinct_test_events"] >= 5 for m in populated)
                               else "insufficient_evidence",
            "prediction_ready": False
        })
    output["summary"] = summary
    output["status"] = "ok" if any(m["paired_observations"] for m in summary) else "insufficient_data"
    return output


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
    print("Rolling opponent validation:", result["status"], len(result["windows"]))


if __name__ == "__main__":
    main()
