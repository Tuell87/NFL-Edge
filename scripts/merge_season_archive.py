#!/usr/bin/env python3
"""Merge independently collected complete game groups into history.json.

Never append a partial game or duplicate event. The archive is optional:
missing/failed archival data is explicitly reported, never synthesized.
"""
import json
from collections import defaultdict
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location('archive_check', 'scripts/check_season_archive.py')
archive_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive_check)

HISTORY = Path("data/history.json")
ARCHIVE = Path("data/archive_2025.json")
ARCHIVE_2024 = Path("data/archive_2024.json")
MAX_COMBINED_ROWS = 50000


def group_games(rows):
    games = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            continue
        event = str(row.get("event_id") or "").strip()
        if event:
            games[event].append(row)
    return games


def merge(current, archive, max_rows=MAX_COMBINED_ROWS, season=2025):
    current_groups = group_games(current.get("rows", []))
    validation = archive_check.inspect(archive, expected_season=season)
    archive_groups = group_games(archive.get("rows", [])) if validation["safe_to_merge"] else {}
    groups = dict(current_groups)
    added = 0
    skipped_cap = 0
    skipped_duplicate = 0
    count = sum(len(g) for g in groups.values())
    for event, records in sorted(archive_groups.items(), key=lambda item:
                                 max(str(r.get("game_date") or "") for r in item[1]),
                                 reverse=True):
        if event in groups:
            skipped_duplicate += 1
            continue
        if count + len(records) > max_rows:
            skipped_cap += 1
            continue
        groups[event] = records
        count += len(records)
        added += 1
    merged_rows = [r for records in sorted(groups.values(), key=lambda records:
                   max(str(r.get("game_date") or "") for r in records),
                   reverse=True) for r in records]
    output = dict(current)
    output["rows"] = merged_rows
    output["games"] = len(groups)
    output["row_limit"] = max_rows
    output["status"] = "ok" if merged_rows else current.get("status", "no_history")
    prefix = f"archive_{season}"
    output[f"{prefix}_status"] = (archive.get("status", "unavailable") if validation["safe_to_merge"] or archive.get("status") != "ok" else "unusable_or_invalid")
    output[f"{prefix}_validation"] = validation
    output[f"{prefix}_games_added"] = added
    output[f"{prefix}_games_skipped_duplicate"] = skipped_duplicate
    output[f"{prefix}_games_skipped_row_cap"] = skipped_cap
    output[f"{prefix}_scoreboard_days_failed"] = archive.get("scoreboard_days_failed")
    output[f"{prefix}_summary_attempts"] = archive.get("summaries_attempted")
    output["limitations"] = (
        str(current.get("limitations") or "") +
        f" {season} archive merged by complete ESPN event IDs only; season coverage "
        "may be incomplete due failed scoreboard/summary requests or row caps. "
        "Archive unavailable does not imply no historical games.")
    return output


def main():
    try:
        current = json.loads(HISTORY.read_text())
        if not isinstance(current, dict):
            raise ValueError("invalid current history")
    except (OSError, ValueError, TypeError):
        current = {"status": "no_history", "rows": [], "games": 0}
    try:
        archive = json.loads(ARCHIVE.read_text())
        if not isinstance(archive, dict):
            raise ValueError("invalid archive")
    except (OSError, ValueError, TypeError):
        archive = {"status": "unavailable", "rows": []}
    output = merge(current, archive)
    try:
        archive_2024 = json.loads(ARCHIVE_2024.read_text())
        if not isinstance(archive_2024, dict):
            raise ValueError("invalid 2024 archive")
    except (OSError, ValueError, TypeError):
        archive_2024 = {"status": "unavailable", "rows": []}
    output = merge(output, archive_2024, season=2024)
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(output, indent=2))
    print("Combined history:", output["games"], "games;",
          output["archive_2025_games_added"], "2025 games;",
          output["archive_2024_games_added"], "2024 games added")


if __name__ == "__main__":
    main()
