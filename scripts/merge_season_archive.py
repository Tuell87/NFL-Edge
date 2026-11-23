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


def merge(current, archive, max_rows=MAX_COMBINED_ROWS):
    current_groups = group_games(current.get("rows", []))
    validation = archive_check.inspect(archive)
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
    output["archive_2025_status"] = (archive.get("status", "unavailable") if validation["safe_to_merge"] or archive.get("status") != "ok" else "unusable_or_invalid")
    output["archive_2025_validation"] = validation
    output["archive_2025_games_added"] = added
    output["archive_2025_games_skipped_duplicate"] = skipped_duplicate
    output["archive_2025_games_skipped_row_cap"] = skipped_cap
    output["archive_2025_scoreboard_days_failed"] = archive.get("scoreboard_days_failed")
    output["archive_2025_summary_attempts"] = archive.get("summaries_attempted")
    output["limitations"] = (
        str(current.get("limitations") or "") +
        " 2025 archive merged by complete ESPN event IDs only; season coverage "
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
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(output, indent=2))
    print("Combined history:", output["games"], "games;",
          output["archive_2025_games_added"], "2025 archive games added")


if __name__ == "__main__":
    main()
