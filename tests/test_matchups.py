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
    def test_fresh_unique_roster_id_corrects_team_and_conflicts_are_excluded(self):
        now = datetime(2026, 11, 22, tzinfo=timezone.utc)
        games = [
            {"id": "g1", "start": "2026-12-01T20:00:00Z", "state": "pre",
             "home": {"name": "Old"}, "away": {"name": "Old opponent"}},
            {"id": "g2", "start": "2026-12-02T20:00:00Z", "state": "pre",
             "home": {"name": "New"}, "away": {"name": "New opponent"}},
        ]
        players = [{"player": "Example", "player_id": "123", "team": "Old",
                    "market": "player_rush_yds", "games": 5}]
        old = {"team": "Old", "status": "listed", "athletes": [{"player_id": "456"}]}
        new = {"team": "New", "status": "listed", "athletes": [{"player_id": "123"}]}
        snapshot = {"checked_at": now.isoformat(), "teams": [old, new]}
        result = mod.build(games, players, now, snapshot)
        self.assertEqual([(row["team"], row["opponent"], row["team_source"]) for row in result],
                         [("New", "New opponent", "espn_roster_snapshot")])
        self.assertFalse(result[0]["prediction_ready"])
        self.assertEqual(result[0]["injury_status"], "unverified")
        old["athletes"].append({"player_id": "123"})
        self.assertEqual(mod.build(games, players, now, snapshot), [])
        snapshot["checked_at"] = "2026-11-19T00:00:00Z"
        result = mod.build(games, players, now, snapshot)
        self.assertEqual([(row["team"], row["team_source"]) for row in result],
                         [("Old", "historical_box_score")])

if __name__=="__main__":
    unittest.main()
