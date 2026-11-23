import importlib.util
import unittest
spec=importlib.util.spec_from_file_location("quality","scripts/build_history_quality.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class QualityTests(unittest.TestCase):
    def test_counts_and_deduplicates(self):
        rows=[{"event_id":"g1","player_id":"p1","game_date":"2026-10-01T18:00:00Z","category":"rushing"},
              {"event_id":"g1","player_id":"p1","game_date":"2026-10-01T18:00:00Z","category":"receiving"},
              {"event_id":"g2","player_id":"p2","game_date":"2026-10-08T18:00:00Z","category":"rushing"}]
        r=mod.build({"status":"ok","rows":rows,"events_discovered":4,"games":2})
        self.assertEqual(r["unique_events_in_rows"],2)
        self.assertEqual(r["unique_players"],2)
        self.assertEqual(r["discovered_events_without_usable_boxscores"],2)
        self.assertEqual(r["boxscore_extraction_rate"],.5)
        self.assertEqual(r["earliest_game_date"],"2026-10-01")
    def test_no_discovered_games_does_not_invent_rate(self):
        r=mod.build({"status":"no_history","rows":[],"events_discovered":0,"games":0})
        self.assertIsNone(r["boxscore_extraction_rate"])
        self.assertEqual(r["status"],"insufficient_data")
    def test_bad_input_is_safe(self):
        r=mod.build({"status":"ok","rows":"invalid","events_discovered":-1,"games":"none"})
        self.assertEqual(r["stat_rows"],0)
        self.assertIsNone(r["events_discovered"])
if __name__=="__main__":
    unittest.main()
