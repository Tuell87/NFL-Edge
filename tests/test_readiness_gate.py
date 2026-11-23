import importlib.util
import unittest
spec=importlib.util.spec_from_file_location("readiness_gate","scripts/readiness_gate.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class ReadinessGateTests(unittest.TestCase):
    def test_unverified_availability_is_blocked(self):
        r=mod.evaluate({"sample_quality":"sufficient_recent_sample","availability":"unverified","injury_status":"unverified"})
        self.assertFalse(r["prediction_ready"])
        self.assertIn("active_roster_not_verified",r["readiness_blockers"])
        self.assertIn("injury_availability_not_verified",r["readiness_blockers"])
    def test_claimed_clearance_cannot_bypass_missing_source(self):
        r=mod.evaluate({"sample_quality":"sufficient_recent_sample","availability":"verified_active","injury_status":"verified_available","matchup_adjustment":1})
        self.assertFalse(r["prediction_ready"])
        self.assertIn("independent_availability_source_not_integrated",r["readiness_blockers"])
    def test_weak_sample_has_separate_reason(self):
        r=mod.evaluate({"sample_quality":"limited_sample"})
        self.assertIn("historical_sample_not_sufficient",r["readiness_blockers"])
    def test_annotation_preserves_player_identity(self):
        r=mod.annotate([{"player_id":"123","player":"Example"}])
        self.assertEqual(r[0]["player_id"],"123")
        self.assertEqual(r[0]["readiness_status"],"research_only")
if __name__=="__main__":
    unittest.main()
