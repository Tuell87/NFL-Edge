import importlib.util
import unittest
from datetime import datetime, timezone

spec = importlib.util.spec_from_file_location("integrity", "scripts/build_feed_integrity.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NOW = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)


class FeedIntegrityTests(unittest.TestCase):
    def test_duplicate_stat_category_and_missing_ids_are_reported(self):
        history = {"status": "ok", "checked_at": NOW.isoformat(), "games": 1,
                   "rows": [
                       {"event_id": "e1", "player_id": "p1", "category": "rushing"},
                       {"event_id": "e1", "player_id": "p1", "category": "rushing"},
                       {"event_id": "e1", "player_id": "", "category": "receiving"}]}
        result = mod.build(history, {"games": []}, {"checked_at": NOW.isoformat()},
                           {"matchups": []}, NOW)
        self.assertEqual(result["history_duplicate_keys"], 1)
        self.assertEqual(result["history_rows_missing_ids"], 1)
        self.assertEqual(result["history_distinct_events"], 1)
        self.assertIn("history_duplicate_event_player_category", result["warnings"])

    def test_impossible_game_count_fails_closed(self):
        history = {"status": "ok", "checked_at": NOW.isoformat(), "games": 0,
                   "rows": [{"event_id": "e1", "player_id": "p1", "category": "rushing"}]}
        result = mod.build(history, {"games": []}, {}, {"matchups": []}, NOW)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("history_game_count_less_than_distinct_events", result["errors"])

    def test_stale_roster_is_warning_not_fabricated_inactive(self):
        history = {"status": "no_history", "rows": []}
        result = mod.build(history, {"games": []},
                           {"checked_at": "2026-11-01T00:00:00Z", "teams": []},
                           {"matchups": []}, NOW)
        self.assertIn("roster_snapshot_missing_or_stale", result["warnings"])
        self.assertEqual(result["status"], "ok")

    def test_unverified_matchup_cannot_be_prediction_ready(self):
        history = {"status": "no_history", "rows": []}
        result = mod.build(history, {}, {}, {"matchups": [
            {"player_id": "p1", "game_start": "2026-12-01T00:00:00Z",
             "prediction_ready": True}]}, NOW)
        self.assertIn("unverified_matchup_prediction_enabled", result["errors"])


if __name__ == "__main__":
    unittest.main()
