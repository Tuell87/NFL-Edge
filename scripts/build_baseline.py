#!/usr/bin/env python3
"""Historical prop hit rates for exploration, not predictive probabilities."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location("sample_quality", "scripts/sample_quality.py")
sample_quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample_quality)

spec_observations = importlib.util.spec_from_file_location("observations", "scripts/observations.py")
observation_filter = importlib.util.module_from_spec(spec_observations)
spec_observations.loader.exec_module(observation_filter)

HISTORY = Path("data/history.json")
OUTPUT = Path("data/baseline.json")
# ESPN game box score labels vary by category; use only unambiguous yards labels.
CATEGORIES = {"rushing": "player_rush_yds", "receiving": "player_reception_yds"}
MIN_GAMES = 2


def parse_yards(row):
    category = str(row.get("category", "")).lower()
    if category not in CATEGORIES:
        return None
    stats = row.get("stats") or {}
    value = stats.get("YDS")
    if value is None:
        return None
    try:
        number = float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None
    return (CATEGORIES[category], number) if math.isfinite(number) else None


def build(rows):
    groups = {}
    for row in observation_filter.unique_rows(rows):
        parsed = parse_yards(row)
        if not parsed:
            continue
        market, yards = parsed
        player_id = str(row.get("player_id") or "").strip()
        event_id = str(row.get("event_id") or "").strip()
        if not player_id or not event_id:
            continue
        key = (player_id, market)
        # Deduplicate one observation per game, category and player.
        groups.setdefault(key, {})[event_id] = {
            "yards": yards, "date": row.get("game_date") or "",
            "player": row.get("player") or "", "team": row.get("team") or "",
        }
    output = []
    for (player_id, market), observations in groups.items():
        games = sorted(observations.values(), key=lambda r: r["date"])
        if len(games) < MIN_GAMES:
            continue
        values = [g["yards"] for g in games]
        output.append({
            "player_id": player_id, "player": games[-1]["player"],
            "team": games[-1]["team"], "market": market,
            "games": len(values), "average_yards": round(sum(values) / len(values), 2),
            "min_yards": min(values), "max_yards": max(values),
            "game_yards": values, "last_game_date": games[-1]["date"],
        })
    return sorted(output, key=lambda r: (r["player"].lower(), r["market"]))


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(HISTORY.read_text())
        rows = build(data.get("rows") or []) if data.get("status") == "ok" else []
        result = {
            "status": "ok" if rows else "insufficient_data",
            "source": "ESPN historical box-score snapshot",
            "history_checked_at": data.get("checked_at"),
            "minimum_games": MIN_GAMES, "players": sample_quality.annotate(rows, datetime.now(timezone.utc)),
            "disclaimer": "Descriptive recent-game results only. Not a forecast, calibrated probability, or recommendation."
        }
    except Exception:
        result = {"status": "unavailable", "players": [], "disclaimer": "No historical data available."}
    OUTPUT.write_text(json.dumps(result, indent=2))
    print(f"Descriptive baseline: {result['status']} ({len(result['players'])} player-market rows)")


if __name__ == "__main__":
    main()
