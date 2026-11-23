import importlib.util
import unittest
from datetime import datetime, timezone
spec=importlib.util.spec_from_file_location("matchups","scripts/build_matchups.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class MatchupTests(unittest.TestCase):
    def test_opponent_join_and_unverified_injury(self):
        games=[{"id":"g","start":"2026-12-01T20:00:00Z","state":"pre",
                "home":{"name":"Team A"},"away":{"name":"Team B"}}]
        players=[{"player":"Example","player_id":"123","team":"Team A","market":"player_rush_yds","games":5}]
        result=mod.build(games,players,datetime(2026,11,22,tzinfo=timezone.utc))
        self.assertEqual(result[0]["opponent"],"Team B")
        self.assertEqual(result[0]["player_id"],"123")
        self.assertEqual(result[0]["injury_status"],"unverified")
        self.assertFalse(result[0]["prediction_ready"])
    def test_excludes_started_and_unmatched(self):
        games=[{"id":"g","start":"2026-11-01T20:00:00Z","state":"post",
                "home":{"name":"Team A"},"away":{"name":"Team B"}}]
        players=[{"player":"Example","team":"Team A"}]
        self.assertEqual(mod.build(games,players,datetime(2026,11,22,tzinfo=timezone.utc)),[])
if __name__=="__main__":
    unittest.main()
