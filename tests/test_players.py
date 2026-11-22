import importlib.util
import unittest
spec = importlib.util.spec_from_file_location("fetch_players", "scripts/fetch_players.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PlayerTests(unittest.TestCase):
    def test_extract_box_scores(self):
        event={"id":"123","name":"Away at Home","date":"2026-11-22"}
        summary={"boxscore":{"players":[{"team":{"displayName":"Home"},"statistics":[{"name":"rushing","labels":["CAR","YDS","TD"],"athletes":[{"athlete":{"id":"9","displayName":"Test Runner"},"stats":["12","83","1"]}]}]}]}}
        rows=mod.extract(event,summary)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["player"],"Test Runner")
        self.assertEqual(rows[0]["stats"]["YDS"],"83")
        self.assertEqual(rows[0]["category"],"rushing")

    def test_missing_stats_ignored(self):
        self.assertEqual(mod.extract({},{}),[])
        self.assertEqual(mod.extract({},{"boxscore":{"players":[{"statistics":[{"athletes":[{"athlete":{"displayName":"X"},"stats":[]}]}]}]}}),[])

if __name__=="__main__":
    unittest.main()
