import importlib.util
import unittest
spec=importlib.util.spec_from_file_location("holdout","scripts/evaluate_holdout.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
def row(event,date,yards,player="1"):
    return {"event_id":str(event),"game_date":date,"player_id":player,"category":"rushing","stats":{"YDS":str(yards)}}
class HoldoutTests(unittest.TestCase):
    def test_requires_eight_distinct_dates(self):
        self.assertEqual(mod.evaluate([row(i,f"2026-09-{i+1:02d}",20) for i in range(7)])["status"],"insufficient_data")
    def test_only_last_quarter_dates_scored(self):
        rows=[row(i,f"2026-09-{i+1:02d}",20 if i<8 else 100) for i in range(12)]
        result=mod.evaluate(rows)
        self.assertEqual(result["holdout_start"],"2026-09-10")
        self.assertEqual(result["holdout_dates"],3)
        metric=next(m for m in result["metrics"] if m["line"]==24.5)
        self.assertEqual(metric["observations"],3)
        self.assertEqual(metric["observed_over_rate"],1)
    def test_same_day_never_training(self):
        rows=[row(i,f"2026-09-{i+1:02d}",20) for i in range(9)]
        rows.extend([row("nine-a","2026-09-10",100),row("nine-b","2026-09-10",100)])
        result=mod.evaluate(rows)
        metric=next(m for m in result["metrics"] if m["line"]==24.5)
        self.assertEqual(metric["observations"],4)
        self.assertEqual(metric["observed_over_rate"],0.5)
    def test_missing_dates_do_not_crash(self):
        self.assertEqual(mod.evaluate([row("a","not-a-date",20)])["status"],"insufficient_data")
if __name__=="__main__":
    unittest.main()
