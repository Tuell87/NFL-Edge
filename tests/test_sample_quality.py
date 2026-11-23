import importlib.util
import unittest
from datetime import datetime,timezone
spec=importlib.util.spec_from_file_location("sample_quality","scripts/sample_quality.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NOW=datetime(2026,11,22,20,tzinfo=timezone.utc)
class SampleQualityTests(unittest.TestCase):
    def test_recent_sufficient_sample_is_not_a_prediction(self):
        x=mod.assess({"games":7,"last_game_date":"2026-11-15T20:00:00Z"},NOW)
        self.assertEqual(x["sample_quality"],"sufficient_recent_sample")
        self.assertFalse(x["prediction_ready"])
    def test_small_sample(self):
        x=mod.assess({"games":3,"last_game_date":"2026-11-15T20:00:00Z"},NOW)
        self.assertIn("fewer_than_five_games",x["sample_quality_reasons"])
    def test_stale_or_future(self):
        for date in ("2026-09-01T20:00:00Z","2026-12-01T20:00:00Z","unknown"):
            self.assertEqual(mod.assess({"games":8,"last_game_date":date},NOW)["sample_quality"],"limited_sample")
    def test_missing_timezone(self):
        self.assertEqual(mod.assess({"games":8,"last_game_date":"2026-11-15T20:00:00"},NOW)["sample_quality"],"limited_sample")
if __name__=="__main__":
    unittest.main()
