import importlib.util
import unittest

spec = importlib.util.spec_from_file_location("rolling", "scripts/evaluate_opponent_rolling.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sample(days=20):
    rows = []
    for day in range(1, days + 1):
        for i in range(12):
            for team, yards in (("A", 25 + day), ("B", 40 + day)):
                rows.append({"event_id": str(day), "game_date": f"2026-09-{day:02d}",
                             "player_id": f"{team}{i}", "team": team,
                             "category": "rushing", "stats": {"YDS": str(yards)}})
    return rows


class RollingTests(unittest.TestCase):
    def test_insufficient_dates_fail_closed(self):
        result = mod.evaluate(sample(11))
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["windows"], [])
        self.assertFalse(result["prediction_ready"])

    def test_three_non_overlapping_windows(self):
        result = mod.evaluate(sample(20))
        self.assertEqual(len(result["windows"]), 3)
        self.assertEqual([w["observed_test_dates"] for w in result["windows"]], [5, 5, 5])
        self.assertEqual(result["windows"][0]["start"], "2026-09-06")
        self.assertEqual(result["windows"][0]["end_exclusive"], "2026-09-11")
        self.assertEqual(result["windows"][1]["start"], "2026-09-11")
        self.assertEqual(result["windows"][2]["start"], "2026-09-16")
        self.assertIsNone(result["windows"][2]["end_exclusive"])
        self.assertFalse(result["prediction_ready"])
        self.assertFalse(result["summary"][0]["prediction_ready"])

    def test_future_results_do_not_affect_first_window(self):
        original = sample(20)
        modified = [dict(r, stats={"YDS": "900"}) if r["game_date"] >= "2026-09-16"
                    else r for r in original]
        first = mod.evaluate(original)
        second = mod.evaluate(modified)
        self.assertEqual(first["windows"][0], second["windows"][0])

    def test_single_team_cannot_produce_false_comparison(self):
        only_one = [r for r in sample(20) if r["team"] == "A"]
        result = mod.evaluate(only_one)
        self.assertEqual(result["status"], "insufficient_data")


if __name__ == "__main__":
    unittest.main()
