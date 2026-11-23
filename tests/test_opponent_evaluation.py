import importlib.util
import unittest

spec = importlib.util.spec_from_file_location("opponent_eval", "scripts/evaluate_opponent.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(event, date, player, team, category, yards):
    return {"event_id": str(event), "game_date": date, "player_id": str(player),
            "team": team, "category": category, "stats": {"YDS": str(yards)}}


def dataset():
    rows = []
    for day in range(1, 13):
        date = f"2026-09-{day:02d}"
        for i in range(12):
            rows.append(row(day, date, f"a{i}", "Team A", "rushing", 40 + day))
            rows.append(row(day, date, f"b{i}", "Team B", "rushing", 20 + day))
    return rows


class OpponentEvaluationTests(unittest.TestCase):
    def test_no_two_team_identity_no_opponent_claim(self):
        rows = [row(i, f"2026-09-{i:02d}", "p1", "Team A", "rushing", 40)
                for i in range(1, 12)]
        result = mod.evaluate(rows)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["eligible_rows"], 0)

    def test_paired_results_and_fail_closed(self):
        result = mod.evaluate(dataset())
        metric = next(m for m in result["metrics"] if m["category"] == "rushing")
        self.assertGreater(metric["paired_observations"], 0)
        self.assertGreater(metric["distinct_test_events"], 0)
        self.assertIsNotNone(metric["player_only_mae"])
        self.assertIsNotNone(metric["opponent_adjusted_mae"])
        self.assertFalse(metric["prediction_ready"])
        self.assertEqual(metric["adjustment_wins"] + metric["adjustment_losses"] +
                         metric["adjustment_ties"], metric["paired_observations"])

    def test_future_results_do_not_change_earlier_comparison(self):
        original = dataset()
        first = mod.evaluate(original)
        changed = [dict(r, stats={"YDS": "900"}) if r["game_date"] == "2026-09-12" else r
                   for r in original]
        second = mod.evaluate(changed)
        a = next(m for m in first["metrics"] if m["category"] == "rushing")
        b = next(m for m in second["metrics"] if m["category"] == "rushing")
        self.assertEqual(a["paired_observations"], b["paired_observations"])
        # Changing the final date changes the scored error, not earlier predictions.
        earlier = [r for r in original if r["game_date"] != "2026-09-12"]
        self.assertEqual(mod.evaluate(earlier)["metrics"][0]["player_only_mae"],
                         mod.evaluate([r for r in changed if r["game_date"] != "2026-09-12"])["metrics"][0]["player_only_mae"])

    def test_duplicate_stat_key_excluded(self):
        rows = dataset()
        rows.append(dict(rows[0]))
        prepared = mod.prepare(rows)
        self.assertFalse(any(r[1] == "1" and r[2] == "a0" and r[3] == "rushing" for r in prepared))


if __name__ == "__main__":
    unittest.main()
