import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


quality = load("roster_quality", "scripts/build_roster_quality.py")
health = load("generated_health", "scripts/check_generated_health.py")


class RosterQualityTests(unittest.TestCase):
    def test_coverage_counts_do_not_imply_readiness(self):
        rosters = {"status": "ok", "teams": [
            {"status": "listed", "athletes": [{"player_id": "1"}, {"player_id": "2"}]},
            {"status": "fetch_failed", "athletes": []}]}
        matchups = {"matchups": [
            {"player_id": "1", "team": "A", "roster_listing": "listed"},
            {"player_id": "1", "team": "A", "roster_listing": "listed"},
            {"player_id": "3", "team": "B", "roster_listing": "unavailable"}]}
        result = quality.build(rosters, matchups)
        self.assertEqual(result["teams_fetch_failed"], 1)
        self.assertEqual(result["unique_athlete_ids"], 2)
        self.assertEqual(result["upcoming_player_team_pairs"], 2)
        self.assertEqual(result["matchup_listed"], 2)
        self.assertFalse(result["prediction_ready"])

    def test_generated_health_blocks_recommendations(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            payloads = {
                "feed_integrity.json": {"status": "ok", "warnings": [], "errors": []},
                "rosters.json": {"status": "ok", "teams": [], "teams_with_rosters": 0},
                "roster_quality.json": {"status": "ok", "teams_requested": 0,
                                        "teams_with_listings": 0, "prediction_ready": False},
                "matchups.json": {"status": "ok", "matchups": [{"prediction_ready": False}]},
                "history.json": {"status": "ok", "rows": []},
                "history_quality.json": {"status": "ok", "categories": []},
                "holdout.json": {"status": "insufficient_data", "metrics": []},
                "opponent_evaluation.json": {"status": "insufficient_data", "metrics": []},
                "opponent_holdout.json": {"status": "insufficient_data", "metrics": []},
                "opponent_rolling.json": {"status": "insufficient_data", "windows": [], "prediction_ready": False},
                "opponent_seasons.json": {"status": "insufficient_data", "tests": [], "prediction_ready": False},
                "market_audit.json": {"status": "ok", "rows": [
                    {"prediction_ready": False, "recommended": True}]},
            }
            for filename, document in payloads.items():
                (path / filename).write_text(json.dumps(document))
            failures, warnings = health.validate(path)
            self.assertTrue(any("cannot be recommended" in msg for msg in failures))
            self.assertTrue(any("roster coverage unavailable" in msg for msg in warnings))
            payloads["market_audit.json"]["rows"][0]["recommended"] = False
            (path / "market_audit.json").write_text(json.dumps(payloads["market_audit.json"]))
            failures, _ = health.validate(path)
            self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
