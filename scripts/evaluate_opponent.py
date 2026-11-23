#!/usr/bin/env python3
"""Leakage-safe research comparison of player-only and opponent-context yardage means.

An opponent adjustment derived from observed player box scores can reflect
player mix, schedule, and missing data; it is NOT a defensive rating or betting
edge. Every comparison uses information strictly earlier than the target date.
"""
import importlib.util
import json
import random
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location("baseline_eval", "scripts/evaluate_baseline.py")
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)

OUTPUT = Path("data/opponent_evaluation.json")
MIN_PLAYER_GAMES = 5
MIN_OPPONENT_GAMES = 3
MIN_OPPONENT_ROWS = 20
SHRINKAGE_ROWS = 30
MIN_FACTOR = 0.75
MAX_FACTOR = 1.25


def date_key(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        return None


def prepare(rows):
    """Only two-team events with stable identities can supply opponent context."""
    by_event = defaultdict(set)
    for row in rows:
        if isinstance(row, dict) and row.get("event_id") and row.get("team"):
            by_event[str(row["event_id"])].add(str(row["team"]).strip())
    opponents = {}
    for event, teams in by_event.items():
        if len(teams) == 2 and all(teams):
            a, b = sorted(teams)
            opponents[(event, a)] = b
            opponents[(event, b)] = a
    unique = {}
    ambiguous = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        parsed = baseline.parse_yards(row)
        event = str(row.get("event_id") or "").strip()
        player = str(row.get("player_id") or "").strip()
        team = str(row.get("team") or "").strip()
        date = date_key(row.get("game_date"))
        if not parsed or not event or not player or not team or not date:
            continue
        opponent = opponents.get((event, team))
        if not opponent:
            continue
        category, yards = parsed
        key = (event, player, category)
        # Ambiguous duplicate observations are excluded, not overwritten.
        if key in unique:
            ambiguous.add(key)
        else:
            unique[key] = (date, event, player, category, team, opponent, yards)
    return [value for key, value in unique.items() if key not in ambiguous]


BOOTSTRAP_REPLICATES = 1000
BOOTSTRAP_SEED = 20261123


def event_cluster_interval(pairs, replicates=BOOTSTRAP_REPLICATES, seed=BOOTSTRAP_SEED):
    """Percentile interval for paired MAE improvement, resampling entire events.

    Descriptive uncertainty only; sampled events are not independent seasons,
    and the historical sample is not randomly selected.
    """
    clusters = defaultdict(list)
    for player_error, adjusted_error, event, _ in pairs:
        clusters[event].append(player_error - adjusted_error)
    if len(clusters) < 5:
        return None
    events = sorted(clusters)
    rng = random.Random(seed)
    estimates = []
    for _ in range(replicates):
        chosen = [clusters[events[rng.randrange(len(events))]]
                  for _ in events]
        errors = [value for group in chosen for value in group]
        estimates.append(sum(errors) / len(errors))
    estimates.sort()
    low = estimates[int(0.025 * (len(estimates) - 1))]
    high = estimates[int(0.975 * (len(estimates) - 1))]
    return round(low, 4), round(high, 4)


class HistoricalIndex:
    """Date-sorted prefix sums; every lookup excludes same-date observations."""

    def __init__(self, records):
        ordered = sorted(records, key=lambda r: (r[0], r[1], r[2]))
        self.dates = [r[0] for r in ordered]
        self.sums = [0.0]
        self.distinct_events = [0]
        seen = set()
        for record in ordered:
            self.sums.append(self.sums[-1] + record[6])
            seen.add(record[1])
            self.distinct_events.append(len(seen))

    def prior(self, day):
        count = bisect_left(self.dates, day)
        return count, self.sums[count], self.distinct_events[count]


def evaluate(rows, test_start=None, test_end=None, train_end=None):
    records = prepare(rows)
    by_player = defaultdict(list)
    by_category = defaultdict(list)
    by_opponent = defaultdict(list)
    for record in records:
        date, event, player, category, team, opponent, yards = record
        by_player[(player, category)].append(record)
        by_category[category].append(record)
        by_opponent[(opponent, category)].append(record)
    player_indexes = {key: HistoricalIndex(group) for key, group in by_player.items()}
    opponent_indexes = {key: HistoricalIndex(group) for key, group in by_opponent.items()}
    league_indexes = {key: HistoricalIndex(group) for key, group in by_category.items()}
    pairs = defaultdict(list)
    coverage = CounterLike()
    for (player, category), games in by_player.items():
        for target in games:
            date, event, _, _, team, opponent, actual = target
            if (test_start is not None and date < test_start) or (test_end is not None and date >= test_end):
                continue
            cutoff = min(date, train_end) if train_end is not None else date
            player_count, player_total, _ = player_indexes[(player, category)].prior(cutoff)
            if player_count < MIN_PLAYER_GAMES:
                continue
            coverage.add(category, "player_baseline_eligible")
            opponent_count, opponent_total, opponent_events = opponent_indexes[(opponent, category)].prior(cutoff)
            if opponent_events < MIN_OPPONENT_GAMES or opponent_count < MIN_OPPONENT_ROWS:
                coverage.add(category, "insufficient_opponent_context")
                continue
            league_count, league_total, _ = league_indexes[category].prior(cutoff)
            if not league_count:
                continue
            league_mean = league_total / league_count
            if league_mean <= 0:
                coverage.add(category, "invalid_league_reference")
                continue
            opponent_mean = opponent_total / opponent_count
            raw_factor = opponent_mean / league_mean
            weight = opponent_count / (opponent_count + SHRINKAGE_ROWS)
            factor = max(MIN_FACTOR, min(MAX_FACTOR, 1 + weight * (raw_factor - 1)))
            player_mean = player_total / player_count
            adjusted = player_mean * factor
            pairs[category].append((abs(actual - player_mean),
                                    abs(actual - adjusted), event, date.isoformat()))
            coverage.add(category, "paired_observations")
    metrics = []
    for category in ("rushing", "receiving"):
        sample = pairs[category]
        n = len(sample)
        base = sum(item[0] for item in sample) / n if n else None
        adj = sum(item[1] for item in sample) / n if n else None
        interval = event_cluster_interval(sample)
        metrics.append({
            "category": category,
            "paired_observations": n,
            "distinct_test_events": len({r[2] for r in sample}),
            "distinct_test_dates": len({r[3] for r in sample}),
            "player_only_mae": round(base, 4) if base is not None else None,
            "opponent_adjusted_mae": round(adj, 4) if adj is not None else None,
            "mae_improvement_yards": round(base - adj, 4) if n else None,
            "improvement_interval_95_low": interval[0] if interval else None,
            "improvement_interval_95_high": interval[1] if interval else None,
            "uncertainty_method": "Event-cluster bootstrap, 1000 fixed-seed resamples; descriptive only",
            "adjustment_wins": sum(r[1] < r[0] for r in sample),
            "adjustment_losses": sum(r[1] > r[0] for r in sample),
            "adjustment_ties": sum(r[1] == r[0] for r in sample),
            "player_baseline_eligible": coverage.get(category, "player_baseline_eligible"),
            "insufficient_opponent_context": coverage.get(category, "insufficient_opponent_context"),
            "evidence_status": "preliminary" if n >= 100 and len({r[2] for r in sample}) >= 20
                               else "insufficient_evidence",
            "prediction_ready": False,
        })
    return {
        "status": "ok" if any(m["paired_observations"] for m in metrics) else "insufficient_data",
        "eligible_rows": len(records),
        "test_start": test_start.isoformat() if test_start else None,
        "test_end_exclusive": test_end.isoformat() if test_end else None,
        "training_end_exclusive": train_end.isoformat() if train_end else None,
        "metrics": metrics,
        "method": "Paired chronological player mean vs shrunken opponent allowed-yards ratio; strictly earlier dates, >=5 prior player games, >=3 distinct prior opponent games and >=20 prior opponent player rows, 30-row shrinkage, factor clipped to 0.75–1.25.",
        "limitations": "Research-only descriptive comparison using the same historical sample. Opponent ratios reflect player mix, offensive usage, schedules, and incomplete box scores; not adjusted for injuries, opponent defensive strength, bookmaker lines, or game-day roster. Comparisons are correlated across players and games. Event-cluster bootstrap intervals are descriptive only and do not account for season selection, model choice, or future distribution shift; no verified betting edge."
    }


class CounterLike:
    def __init__(self):
        self.counts = defaultdict(int)

    def add(self, category, name):
        self.counts[(category, name)] += 1

    def get(self, category, name):
        return self.counts[(category, name)]


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
    print("Opponent comparison:", result["status"],
          sum(m["paired_observations"] for m in result["metrics"]))


if __name__ == "__main__":
    main()
