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
MIN_HOLDOUT_OBSERVATIONS = 30
MIN_HOLDOUT_DATES = 4
CALIBRATION_EDGES = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
MIN_BIN_OBSERVATIONS = 30

def calibration_bins(scores, category_filter=None, line_filter=None):
    """Bucket held-out estimates only; never mix training outcomes into bins."""
    buckets = [[] for _ in range(len(CALIBRATION_EDGES)-1)]
    for (category, line), pairs in scores.items():
        if category_filter is not None and category != category_filter:
            continue
        if line_filter is not None and line != line_filter:
            continue
        for probability, outcome in pairs:
            if probability is None or not 0 <= probability <= 1 or outcome not in (0, 1):
                continue
            index = min(int(probability * 5), 4)
            buckets[index].append((probability, outcome))
    result = []
    for index, pairs in enumerate(buckets):
        n = len(pairs)
        result.append({"range_start":CALIBRATION_EDGES[index],
                       "range_end":CALIBRATION_EDGES[index+1],
                       "observations":n,
                       "mean_predicted":round(sum(p for p, _ in pairs)/n, 4) if n else None,
                       "observed_rate":round(sum(y for _, y in pairs)/n, 4) if n else None,
                       "evidence_status":"preliminary" if n >= MIN_BIN_OBSERVATIONS else "insufficient_evidence"})
    return result


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
        return {"status":"insufficient_data","holdout_start":None,"observations":0,"metrics":[],"calibration_bins":[],"calibration_by_market":{},"calibration_by_threshold":{},"calibration_by_market_threshold":{}}
    cut = max(1, int(len(days) * (1-HOLDOUT_FRACTION)))
    if cut >= len(days):
        cut = len(days)-1
    holdout_start = days[cut]
    scores = defaultdict(list)
    training = defaultdict(list)
    for (_, category), games in groups.items():
        for date, actual in games.values():
            if date < holdout_start:
                for line in prob.THRESHOLDS:
                    training[(category, line)].append(int(actual > line))
    reference = {key: (sum(values) + 2) / (len(values) + 4)
                 for key, values in training.items() if values}
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
        reference_p = reference.get((category, line))
        evidence_ok = n >= MIN_HOLDOUT_OBSERVATIONS and (len(days)-cut) >= MIN_HOLDOUT_DATES
        metrics.append({"category":category,"line":line,"observations":n,
                        "evidence_status":"preliminary" if evidence_ok else "insufficient_holdout_evidence",
                        "minimum_observations_required":MIN_HOLDOUT_OBSERVATIONS,
                        "minimum_holdout_dates_required":MIN_HOLDOUT_DATES,
                        "prediction_ready":False,
                        "brier":round(sum((p-y)**2 for p,y in pairs)/n,4),
                        "reference_50_brier":round(sum((.5-y)**2 for p,y in pairs)/n,4),
                        "training_rate_reference":round(reference_p,4) if reference_p is not None else None,
                        "training_rate_brier":round(sum((reference_p-y)**2 for p,y in pairs)/n,4) if reference_p is not None else None,
                        "observed_over_rate":round(sum(y for _,y in pairs)/n,4),
                        "mean_estimated_probability":round(sum(p for p,_ in pairs)/n,4)})
    return {"status":"ok" if metrics else "insufficient_data",
            "holdout_start":holdout_start.isoformat(),
            "holdout_dates":len(days)-cut,
            "observations":sum(m["observations"] for m in metrics),
            "evidence_status":"preliminary" if metrics and all(m["evidence_status"]=="preliminary" for m in metrics) else "insufficient_holdout_evidence",
            "metrics":metrics,
            "calibration_bins":calibration_bins(scores),
            "calibration_by_market":{category:calibration_bins(scores, category)
                                     for category in sorted({key[0] for key in scores})},
            "calibration_by_threshold":{str(line):calibration_bins(scores, line_filter=line)
                                        for line in prob.THRESHOLDS},
            "calibration_by_market_threshold":{
                category:{str(line):calibration_bins(scores, category, line)
                          for line in prob.THRESHOLDS}
                for category in sorted({key[0] for key in scores})}}

def main():
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    try:
        source=json.loads(Path("data/history.json").read_text())
        result=evaluate(source.get("rows",[]) if source.get("status")=="ok" else [])
        result["history_checked_at"]=source.get("checked_at")
    except (OSError,ValueError,TypeError):
        result={"status":"unavailable","holdout_start":None,"observations":0,"metrics":[],"calibration_bins":[],"calibration_by_market":{}}
    result["method"]="Chronological last-quarter-of-observed-game-dates holdout; fixed Beta(2,2) prior and five prior games; includes a training-period pooled-rate benchmark with the same smoothing; no tuning on holdout"
    result["limitations"]="Held-out dates are from a bounded historical sample, not a truly untouched future prospective trial. No injury, roster, opponent or sportsbook-line adjustments. Illustrative yardage thresholds; at least 30 observations across at least four held-out dates per metric are required even for preliminary evidence. Pooled calibration bins combine rushing and receiving; separate per-market bins are also reported. Calibration bins pool illustrative thresholds and correlated player observations; a minimum of 30 observations per bin is required for a preliminary label. Observations may be correlated across players and lines. No verified betting edge."
    OUTPUT.write_text(json.dumps(result,indent=2))
    print("Out-of-time holdout:",result["status"],result["observations"])

if __name__=="__main__":
    main()
