import importlib.util
import unittest

spec = importlib.util.spec_from_file_location("archive_merge", "scripts/merge_season_archive.py")
merge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge)


def row(event, day, player):
    return {"event_id": event, "game_date": day, "player_id": player,
            "category": "rushing", "team": "A", "stats": {"YDS": "20"}}


class ArchiveMergeTests(unittest.TestCase):
    def test_merge_complete_events_and_deduplicate(self):
        current = {"status": "ok", "rows": [row("new", "2026-11-01", "p1")],
                   "games": 1}
        archive = {"status": "ok", "rows": [
            row("old", "2025-11-01", "p2"), row("old", "2025-11-01", "p3"),
            row("new", "2025-11-01", "p4")]}
        result = merge.merge(current, archive)
        self.assertEqual(result["games"], 2)
        self.assertEqual(result["archive_2025_games_added"], 1)
        self.assertEqual(result["archive_2025_games_skipped_duplicate"], 1)
        self.assertEqual(len(result["rows"]), 3)

    def test_row_cap_never_truncates_a_game(self):
        current = {"status": "ok", "rows": [row("new", "2026-11-01", "p1")]}
        archive = {"status": "ok", "rows": [
            row("old", "2025-11-01", "p2"), row("old", "2025-11-01", "p3")]}
        result = merge.merge(current, archive, max_rows=2)
        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(result["archive_2025_games_skipped_row_cap"], 1)

    def test_unavailable_archive_never_invents_history(self):
        current = {"status": "no_history", "rows": [], "games": 0}
        result = merge.merge(current, {"status": "fetch_failed", "rows": [
            row("bad", "2025-11-01", "p1")]})
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["archive_2025_status"], "fetch_failed")

    def test_current_game_rows_preserved(self):
        current = {"status": "ok", "rows": [row("current", "2026-11-01", "p1")]}
        result = merge.merge(current, {"status": "ok", "rows": []})
        self.assertEqual(result["rows"], current["rows"])


if __name__ == "__main__":
    unittest.main()
