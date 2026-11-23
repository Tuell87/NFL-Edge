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
    def test_training_reference_excludes_holdout_outcomes(self):
        original=[row(i,f"2026-09-{i+1:02d}",20) for i in range(12)]
        changed=[row(i,f"2026-09-{i+1:02d}",20 if i<9 else 200) for i in range(12)]
        a=mod.evaluate(original)["metrics"]
        b=mod.evaluate(changed)["metrics"]
        m1=next(m for m in a if m["line"]==24.5)
        m2=next(m for m in b if m["line"]==24.5)
        self.assertEqual(m1["training_rate_reference"],m2["training_rate_reference"])
        self.assertNotEqual(m1["training_rate_brier"],m2["training_rate_brier"])
    def test_small_holdout_is_not_sufficient_evidence(self):
        rows=[row(i,f"2026-09-{i+1:02d}",20) for i in range(12)]
        result=mod.evaluate(rows)
        self.assertEqual(result["evidence_status"],"insufficient_holdout_evidence")
        self.assertTrue(all(m["evidence_status"]=="insufficient_holdout_evidence" for m in result["metrics"]))
        self.assertTrue(all(not m["prediction_ready"] for m in result["metrics"]))
    def test_more_dates_and_observations_only_preliminary(self):
        rows=[]
        for i in range(20):
            for p in range(10):
                rows.append(row(f"{i}-{p}",f"2026-09-{i+1:02d}",20+i,player=str(p)))
        result=mod.evaluate(rows)
        self.assertEqual(result["evidence_status"],"preliminary")
        self.assertTrue(all(not m["prediction_ready"] for m in result["metrics"]))
    def test_calibration_bin_boundaries_and_empty_bins(self):
        result=mod.calibration_bins({("rushing",24.5):[(0.0,0),(0.2,1),(0.8,1),(1.0,0)]})
        self.assertEqual([b["observations"] for b in result],[1,1,0,0,2])
        self.assertIsNone(result[2]["observed_rate"])
        self.assertTrue(all(b["evidence_status"]=="insufficient_evidence" for b in result))
    def test_calibration_uses_only_holdout_outcomes(self):
        rows=[row(i,f"2026-09-{i+1:02d}",20 if i<9 else 100) for i in range(12)]
        result=mod.evaluate(rows)
        self.assertEqual(sum(b["observations"] for b in result["calibration_bins"]),result["observations"])
    def test_missing_dates_do_not_crash(self):
        self.assertEqual(mod.evaluate([row("a","not-a-date",20)])["status"],"insufficient_data")
if __name__=="__main__":
    unittest.main()
