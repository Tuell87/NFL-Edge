#!/usr/bin/env python3
"""Out-of-time validation with no model selection on the held-out period.

Reports historical over-probability Brier scores and reference baselines.
No claims about player injuries, upcoming opponents or betting profitability.
"""
import importlib.util
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

spec = importlib.util.spec_from_file_location("prob", "scripts/evaluate_probabilities.py")
prob = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prob)
OUTPUT = Path("data/holdout.json")
MIN_PRIOR = 5
HOLDOUT_FRACTION = 0.25

def valid_date(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z","+00:00")).date()
    except (ValueError, TypeError):
        return None

def evaluate(rows):
    groups = defaultdict(dict)
    dates = set()
    for row in rows:
        parsed = prob.parse_yards(row)
        date = valid_date(row.get("game_date"))
        event = str(row.get("event_id") or "").strip()
        player = str(row.get("player_id") or "").strip()
        if not parsed or not date or not event or not player:
            continue
        category, yards = parsed
        groups[(player, category)][event] = (date, yards)
        dates.add(date)
    days = sorted(dates)
    if len(days) < 8:
        return {"status":"insufficient_data","holdout_start":None,"observations":0,"metrics":[]}
    cut = max(1, int(len(days) * (1-HOLDOUT_FRACTION)))
    if cut >= len(days):
        cut = len(days)-1
    holdout_start = days[cut]
    scores = defaultdict(list)
    for (_, category), games in groups.items():
        ordered = sorted(games.values(), key=lambda item: item[0])
        for date, actual in ordered:
            if date < holdout_start:
                continue
            previous = [yards for old_date, yards in ordered if old_date < date]
            if len(previous) < MIN_PRIOR:
                continue
            for line in prob.THRESHOLDS:
                p = prob.estimate(previous, line)
                outcome = int(actual > line)
                scores[(category, line)].append((p, outcome))
    metrics = []
    for (category, line), pairs in sorted(scores.items()):
        n = len(pairs)
        metrics.append({"category":category,"line":line,"observations":n,
                        "brier":round(sum((p-y)**2 for p,y in pairs)/n,4),
                        "reference_50_brier":round(sum((.5-y)**2 for p,y in pairs)/n,4),
                        "observed_over_rate":round(sum(y for _,y in pairs)/n,4),
                        "mean_estimated_probability":round(sum(p for p,_ in pairs)/n,4)})
    return {"status":"ok" if metrics else "insufficient_data",
            "holdout_start":holdout_start.isoformat(),
            "holdout_dates":len(days)-cut,
            "observations":sum(m["observations"] for m in metrics),
            "metrics":metrics}

def main():
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    try:
        source=json.loads(Path("data/history.json").read_text())
        result=evaluate(source.get("rows",[]) if source.get("status")=="ok" else [])
        result["history_checked_at"]=source.get("checked_at")
    except (OSError,ValueError,TypeError):
        result={"status":"unavailable","holdout_start":None,"observations":0,"metrics":[]}
    result["method"]="Chronological last-quarter-of-observed-game-dates holdout; fixed Beta(2,2) prior and five prior games; no tuning on holdout"
    result["limitations"]="Held-out dates are from a bounded historical sample, not a truly untouched future prospective trial. No injury, roster, opponent or sportsbook-line adjustments. Illustrative yardage thresholds; no verified betting edge."
    OUTPUT.write_text(json.dumps(result,indent=2))
    print("Out-of-time holdout:",result["status"],result["observations"])

if __name__=="__main__":
    main()
