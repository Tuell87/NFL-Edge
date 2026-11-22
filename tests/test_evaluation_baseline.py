import importlib.util
import unittest
spec=importlib.util.spec_from_file_location("evaluate_baseline","scripts/evaluate_baseline.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def row(game,date,yards,player="1",category="rushing"):
    return {"event_id":game,"game_date":date,"player_id":player,"category":category,"stats":{"YDS":str(yards)}}

class EvaluationTests(unittest.TestCase):
    def test_uses_only_prior_games(self):
        result=mod.evaluate([row("a","2026-09-01",10),row("b","2026-09-08",20),row("c","2026-09-15",60)])
        self.assertEqual(result["evaluated_games"],1)
        self.assertEqual(result["metrics"]["rushing"]["mae_yards"],45)

    def test_paired_estimators_use_identical_outcomes(self):
        rows=[row("a","2026-09-01",10),row("b","2026-09-08",20),
              row("c","2026-09-15",30),row("d","2026-09-22",50)]
        m=mod.evaluate(rows)["metrics"]["rushing"]
        self.assertEqual(m["evaluated_games"],2)
        self.assertEqual(m["mae_yards"],22.5)
        self.assertEqual(m["recent_three_mae_yards"],22.5)
        self.assertEqual(m["last_game_mae_yards"],15)

    def test_recent_three_differs_after_four_prior_games(self):
        rows=[row(str(i),f"2026-09-{i+1:02d}",v) for i,v in enumerate([0,0,0,100,100])]
        m=mod.evaluate(rows)["metrics"]["rushing"]
        self.assertEqual(m["evaluated_games"],3)
        self.assertNotEqual(m["mae_yards"],m["recent_three_mae_yards"])

    def test_no_future_leakage(self):
        result=mod.evaluate([row("c","2026-09-15",100),row("a","2026-09-01",10),row("b","2026-09-08",20)])
        self.assertEqual(result["metrics"]["rushing"]["mae_yards"],85)

    def test_insufficient_games(self):
        result=mod.evaluate([row("a","2026-09-01",10)])
        self.assertEqual(result["evaluated_games"],0)
        self.assertIsNone(result["metrics"]["rushing"]["mae_yards"])

    def test_same_day_not_prior(self):
        result=mod.evaluate([row("a","2026-09-01",10),row("b","2026-09-01",20),row("c","2026-09-08",30)])
        self.assertEqual(result["evaluated_games"],1)
        self.assertEqual(result["metrics"]["rushing"]["mae_yards"],15)

if __name__=="__main__":
    unittest.main()
