#!/usr/bin/env python3
"""Compare archived ESPN event IDs with a separately sourced nflverse schedule."""
import argparse
import csv
import json
from pathlib import Path

GAME_TYPES = {"REG", "WC", "DIV", "CON", "SB"}


def compare(history, schedule, seasons):
    observed = {str(row["event_id"]).strip() for row in history["rows"] if row.get("event_id")}
    results = {}
    for season in seasons:
        completed = {}
        for row in schedule:
            if (row["season"] == str(season) and row["game_type"] in GAME_TYPES
                    and row["home_score"].strip() and row["away_score"].strip()):
                game_id = row["game_id"].strip()
                espn_id = row["espn"].strip()
                if not game_id or (game_id in completed and completed[game_id] != espn_id):
                    raise ValueError(f"Missing or conflicting schedule identity for {game_id!r}")
                completed[game_id] = espn_id
        mapped_ids = [espn_id for espn_id in completed.values() if espn_id]
        if len(set(mapped_ids)) != len(mapped_ids):
            raise ValueError(f"Duplicate ESPN event mapping for season {season}")
        results[season] = {
            "completed_schedule_games": len(completed),
            "archive_matches": sum(bool(espn_id) and espn_id in observed for espn_id in completed.values()),
            "archive_missing_games": sorted(game for game, espn_id in completed.items()
                                            if espn_id and espn_id not in observed),
            "schedule_games_without_espn_id": sorted(game for game, espn_id in completed.items() if not espn_id),
        }
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("history", type=Path, help="NFL Edge history.json")
    parser.add_argument("schedule", type=Path, help="nflverse games.csv")
    parser.add_argument("seasons", nargs="+", type=int, help="Completed season years to audit")
    args = parser.parse_args()
    try:
        history = json.loads(args.history.read_text())
        with args.schedule.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            required = {"season", "game_type", "home_score", "away_score", "game_id", "espn"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("Schedule is missing required columns")
            results = compare(history, list(reader), args.seasons)
    except (OSError, KeyError, TypeError, ValueError, AttributeError) as exc:
        parser.error(str(exc))
    print(json.dumps(results, indent=2))
    return int(any(not record["completed_schedule_games"] or record["archive_missing_games"]
                   or record["schedule_games_without_espn_id"] for record in results.values()))


if __name__ == "__main__":
    raise SystemExit(main())
