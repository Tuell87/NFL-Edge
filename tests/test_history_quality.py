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
    def test_sparse_game_player_counts_deduplicate_categories(self):
        rows=[]
        for game,count in [("g1",3),("g2",12),("g3",11)]:
            for i in range(count):
                rows.append({"event_id":game,"player_id":str(i),"category":"rushing"})
                rows.append({"event_id":game,"player_id":str(i),"category":"receiving"})
        r=mod.build({"status":"ok","rows":rows,"events_discovered":3,"games":3})
        self.assertEqual(r["games_with_player_ids"],3)
        self.assertEqual(r["min_unique_players_per_game"],3)
        self.assertEqual(r["median_unique_players_per_game"],11)
        self.assertEqual(r["max_unique_players_per_game"],12)
        self.assertEqual(r["sparse_games_under_ten_players"],1)
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
