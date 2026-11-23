import importlib.util
import unittest
spec=importlib.util.spec_from_file_location("prob","scripts/evaluate_probabilities.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def row(event,date,yards,player="1"):
    return {"event_id":event,"game_date":date,"player_id":player,
            "category":"rushing","stats":{"YDS":str(yards)}}

class ProbabilityTests(unittest.TestCase):
    def test_minimum_prior_games(self):
        self.assertIsNone(mod.estimate([10,20,30,40],24.5))
        self.assertAlmostEqual(mod.estimate([10,20,30,40,50],24.5),5/9)
    def test_only_past_games(self):
        rows=[row(str(i),f"2026-09-{i+1:02d}",10) for i in range(5)]
        rows.append(row("later","2026-09-06",100))
        result=mod.evaluate(list(reversed(rows)))
        metric=next(x for x in result["metrics"] if x["category"]=="rushing" and x["line"]==24.5)
        self.assertEqual(metric["evaluated_games"],1)
        self.assertEqual(metric["observed_over_rate"],1)
        self.assertEqual(metric["mean_probability"],round(2/9,4))
    def test_same_date_not_leaked(self):
        rows=[row(str(i),f"2026-09-{i+1:02d}",10) for i in range(5)]
        rows.extend([row("six","2026-09-06",100),row("seven","2026-09-06",100)])
        result=mod.evaluate(rows)
        metric=next(x for x in result["metrics"] if x["line"]==24.5)
        self.assertEqual(metric["evaluated_games"],2)
        self.assertEqual(metric["mean_probability"],round(2/9,4))
    def test_insufficient_history(self):
        self.assertEqual(mod.evaluate([row("one","2026-09-01",20)])["status"],"insufficient_data")
if __name__=="__main__":
    unittest.main()
