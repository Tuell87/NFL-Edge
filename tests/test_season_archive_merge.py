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
        archive = {"status": "ok", "season": 2025, "games": 2, "rows": [
            row("old", "2025-11-01", "p2"), row("old", "2025-11-01", "p3"),
            row("new", "2025-11-01", "p4")]}
        result = merge.merge(current, archive)
        self.assertEqual(result["games"], 2)
        self.assertEqual(result["archive_2025_games_added"], 1)
        self.assertEqual(result["archive_2025_games_skipped_duplicate"], 1)
        self.assertEqual(len(result["rows"]), 3)

    def test_row_cap_never_truncates_a_game(self):
        current = {"status": "ok", "rows": [row("new", "2026-11-01", "p1")]}
        archive = {"status": "ok", "season": 2025, "games": 1, "rows": [
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

    def test_reject_wrong_season_rows(self):
        current = {"status": "ok", "rows": [row("new", "2026-11-01", "p1")]}
        archive = {"status": "ok", "season": 2025, "games": 1,
                   "rows": [row("bad", "2026-11-01", "p2")]}
        result = merge.merge(current, archive)
        self.assertEqual(result["archive_2025_status"], "unusable_or_invalid")
        self.assertEqual(result["rows"], current["rows"])

    def test_2024_and_2025_archives_can_merge_without_duplicates(self):
        current = {"status": "ok", "rows": [row("2026game", "2026-11-01", "p1")]}
        archive25 = {"status": "ok", "season": 2025, "games": 1,
                     "rows": [row("2025game", "2025-11-01", "p2")]}
        archive24 = {"status": "ok", "season": 2024, "games": 1,
                     "rows": [row("2024game", "2024-11-01", "p3")]}
        result = merge.merge(merge.merge(current, archive25), archive24, season=2024)
        self.assertEqual(result["games"], 3)
        self.assertEqual(result["archive_2024_games_added"], 1)
        self.assertEqual(result["archive_2025_games_added"], 1)
        self.assertEqual(len({r["event_id"] for r in result["rows"]}), 3)

    def test_current_game_rows_preserved(self):
        current = {"status": "ok", "rows": [row("current", "2026-11-01", "p1")]}
        result = merge.merge(current, {"status": "ok", "season": 2025, "games": 0, "rows": []})
        self.assertEqual(result["rows"], current["rows"])


if __name__ == "__main__":
    unittest.main()
