import importlib.util
import unittest
from datetime import datetime, timezone

spec = importlib.util.spec_from_file_location("research_status", "scripts/build_research_status.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NOW = datetime(2026, 11, 23, 14, tzinfo=timezone.utc)


class ResearchStatusTests(unittest.TestCase):
    def test_missing_data_is_fail_closed(self):
        result = mod.build({}, {}, {}, {}, {}, NOW)
        self.assertEqual(result["status"], "research_only")
        self.assertFalse(result["prediction_ready"])
        self.assertIn("historical_box_scores_unavailable", result["readiness_blockers"])
        self.assertIn("cross_season_evaluation_insufficient", result["readiness_blockers"])

    def test_data_coverage_does_not_enable_betting_recommendations(self):
        result = mod.build(
            {"status": "ok", "checked_at": NOW.isoformat(),
             "rows": [{"event_id": "1"}], "games": 1,
             "archive_2025_status": "ok", "archive_2025_games_added": 150},
            {"status": "ok", "checked_at": NOW.isoformat(),
             "teams": [{"status": "listed"}]},
            {"matchups": [{"player_id": "p"}]},
            {"season_coverage": [{"season": 2025, "observed_events": 150},
                                 {"season": 2026, "observed_events": 80}],
             "tests": [{"status": "research_only"}]},
            {"windows": [{"number": 1}]}, NOW)
        self.assertEqual(result["history"]["archive_2025_games_added"], 150)
        self.assertEqual(result["season_tests_with_observations"], 1)
        self.assertFalse(result["prediction_ready"])
        self.assertIn("injury_clearance_not_verified", result["readiness_blockers"])

    def test_stale_data_is_visible(self):
        result = mod.build(
            {"status": "ok", "checked_at": "2026-11-01T00:00:00Z",
             "rows": [{"event_id": "1"}]},
            {"status": "ok", "checked_at": "2026-11-01T00:00:00Z",
             "teams": [{"status": "listed"}]}, {}, {}, {}, NOW)
        self.assertIn("historical_snapshot_stale_or_undated", result["readiness_blockers"])
        self.assertIn("roster_snapshot_stale_or_undated", result["readiness_blockers"])


if __name__ == "__main__":
    unittest.main()
