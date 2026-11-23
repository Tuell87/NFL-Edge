#!/usr/bin/env python3
"""Consistent player-game-category deduplication for research evaluators.

Repeated identical ESPN records are one observation. Conflicting records with
the same stable event/player/category identity are ambiguous and excluded,
not silently overwritten or counted twice. No name-only identity fallback.
"""
import json


def unique_rows(rows):
    seen = {}
    ambiguous = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        event = str(row.get("event_id") or "").strip()
        player = str(row.get("player_id") or "").strip()
        category = str(row.get("category") or "").strip().lower()
        if not event or not player or not category:
            continue
        key = (event, player, category)
        signature = (str(row.get("game_date") or ""),
                     str(row.get("team") or ""),
                     json.dumps(row.get("stats"), sort_keys=True, default=str))
        if key not in seen:
            seen[key] = (signature, row)
        elif seen[key][0] != signature:
            ambiguous.add(key)
    return [row for key, (_, row) in seen.items() if key not in ambiguous]
