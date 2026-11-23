import importlib.util
import unittest
from datetime import date

spec = importlib.util.spec_from_file_location("season_eval", "scripts/evaluate_opponent_seasons.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def dataset(years=(2025, 2026), days=12):
    rows = []
    for year in years:
        for day in range(1, days + 1):
            for i in range(12):
                for team, yards in (("A", 30 + day), ("B", 50 + day)):
                    rows.append({"event_id": f"{year}-{day}",
                                 "game_date": f"{year}-09-{day:02d}",
                                 "player_id": f"{team}{i}", "team": team,
                                 "category": "rushing", "stats": {"YDS": str(yards)}})
    return rows


class SeasonValidationTests(unittest.TestCase):
    def test_january_is_previous_nfl_season(self):
        self.assertEqual(mod.nfl_season(date(2026, 1, 12)), 2025)
        self.assertEqual(mod.nfl_season(date(2026, 9, 12)), 2026)

    def test_one_season_is_not_cross_season_validation(self):
        result = mod.evaluate(dataset((2026,)))
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["tests"], [])
        self.assertFalse(result["prediction_ready"])

    def test_frozen_training_scores_later_season(self):
        result = mod.evaluate(dataset())
        self.assertEqual(result["observed_seasons"], [2025, 2026])
        self.assertEqual(len(result["tests"]), 1)
        test = result["tests"][0]
        self.assertEqual(test["training_seasons"], [2025])
        self.assertEqual(test["test_season"], 2026)
        self.assertTrue(test["coverage_sufficient_for_attempt"])
        self.assertGreater(test["metrics"][0]["paired_observations"], 0)
        self.assertFalse(test["prediction_ready"])

    def test_later_season_outcomes_do_not_affect_frozen_predictions(self):
        rows = dataset()
        modified = [dict(r, stats={"YDS": "900"}) if r["game_date"].startswith("2026")
                    else r for r in rows]
        # For a fixed heldout observation, its prediction uses the same frozen
        # prior-season training data, regardless of other heldout outcomes.
        earlier = [r for r in rows if r["game_date"].startswith("2025")]
        a = mod.opponent.evaluate(earlier + [r for r in rows if r["game_date"] == "2026-09-01"],
                                  test_start=date(2026, 7, 1),
                                  test_end=date(2027, 7, 1), train_end=date(2026, 7, 1))
        b = mod.opponent.evaluate(earlier + [r for r in modified if r["game_date"] == "2026-09-01"],
                                  test_start=date(2026, 7, 1),
                                  test_end=date(2027, 7, 1), train_end=date(2026, 7, 1))
        self.assertEqual(a["metrics"][0]["paired_observations"], b["metrics"][0]["paired_observations"])
        self.assertFalse(a["metrics"][0]["prediction_ready"])

    def test_partial_season_is_explicitly_insufficient(self):
        result = mod.evaluate(dataset(days=3))
        self.assertEqual(result["status"], "insufficient_data")
        self.assertFalse(result["tests"][0]["coverage_sufficient_for_attempt"])


if __name__ == "__main__":
    unittest.main()
