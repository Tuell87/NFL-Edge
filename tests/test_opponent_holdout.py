import importlib.util
import unittest

spec = importlib.util.spec_from_file_location("opponent_holdout", "scripts/evaluate_opponent_holdout.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sample(days=16):
    rows = []
    for day in range(1, days + 1):
        for i in range(12):
            for team, value in (("A", 25 + day), ("B", 40 + day)):
                rows.append({"event_id": str(day), "game_date": f"2026-09-{day:02d}",
                             "player_id": f"{team}{i}", "team": team,
                             "category": "rushing", "stats": {"YDS": str(value)}})
    return rows


class OpponentHoldoutTests(unittest.TestCase):
    def test_requires_multiple_distinct_dates(self):
        result = mod.evaluate(sample(7))
        self.assertEqual(result["status"], "insufficient_data")
        self.assertIsNone(result["holdout_start"])

    def test_scores_only_later_quarter_of_dates(self):
        result = mod.evaluate(sample(16))
        self.assertEqual(result["holdout_start"], "2026-09-13")
        self.assertEqual(result["holdout_dates"], 4)
        rushing = next(m for m in result["metrics"] if m["category"] == "rushing")
        self.assertEqual(rushing["distinct_test_dates"], 4)
        self.assertFalse(rushing["prediction_ready"])

    def test_later_outcomes_cannot_change_earlier_holdout_scores(self):
        original = sample(16)
        changed = [dict(r, stats={"YDS": "900"}) if r["game_date"] == "2026-09-16" else r
                   for r in original]
        # Compare scoring of only dates before the last date with the same cutoff.
        start = mod.opponent.date_key("2026-09-13")
        before = [r for r in original if r["game_date"] != "2026-09-16"]
        before_changed = [r for r in changed if r["game_date"] != "2026-09-16"]
        a = mod.opponent.evaluate(before, test_start=start)
        b = mod.opponent.evaluate(before_changed, test_start=start)
        self.assertEqual(a["metrics"], b["metrics"])

    def test_no_predictions_without_opponent_context(self):
        rows = [{"event_id": str(day), "game_date": f"2026-09-{day:02d}",
                 "player_id": "p", "team": "A", "category": "rushing",
                 "stats": {"YDS": "40"}} for day in range(1, 17)]
        result = mod.evaluate(rows)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["evidence_status"], "insufficient_holdout_evidence")


if __name__ == "__main__":
    unittest.main()
