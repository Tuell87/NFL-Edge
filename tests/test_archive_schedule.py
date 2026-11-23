import importlib.util
import unittest

spec = importlib.util.spec_from_file_location("archive_schedule", "scripts/audit_archive_schedule.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ArchiveScheduleTests(unittest.TestCase):
    def test_counts_unique_completed_games_and_distinguishes_missing_ids(self):
        def game(game_id, espn, game_type="REG", score="0"):
            return {"season": "2025", "game_type": game_type, "game_id": game_id, "espn": espn,
                    "home_score": score, "away_score": "3"}

        schedule = [
            game("seen", "42"), game("seen", "42"), game("missing", "43", "SB"),
            game("unmapped", ""), game("upcoming", "44", score=""), game("preseason", "45", "PRE"),
        ]
        history = {"rows": [{"event_id": "42"}, {"event_id": 42}]}
        self.assertEqual(mod.compare(history, schedule, [2025])[2025], {
            "completed_schedule_games": 3,
            "archive_matches": 1,
            "archive_missing_games": ["missing"],
            "schedule_games_without_espn_id": ["unmapped"],
        })
