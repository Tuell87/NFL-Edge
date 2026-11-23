import importlib.util
import unittest
spec=importlib.util.spec_from_file_location("build_baseline","scripts/build_baseline.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class BaselineTests(unittest.TestCase):
    def test_observed_yards_and_dedup(self):
        def row(game,yards):
            return {"event_id":game,"player_id":"7","player":"Runner","team":"Team","category":"rushing","game_date":"2026-11-01","stats":{"YDS":str(yards)}}
        result=mod.build([row("a",30),row("a",30),row("b",50)])
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["games"],2)
        self.assertEqual(result[0]["average_yards"],40)

    def test_conflicting_game_rows_excluded_not_silently_overwritten(self):
        def row(game,yards):
            return {"event_id":game,"player_id":"7","player":"Runner","team":"Team",
                    "category":"rushing","game_date":"2026-11-01","stats":{"YDS":str(yards)}}
        result=mod.build([row("a",30),row("a",999),row("b",50),row("c",70)])
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["games"],2)
        self.assertEqual(result[0]["average_yards"],60)

    def test_minimum_games(self):
        rows=[{"event_id":"a","player_id":"1","category":"receiving","stats":{"YDS":"70"}}]
        self.assertEqual(mod.build(rows),[])

    def test_invalid_yards(self):
        self.assertIsNone(mod.parse_yards({"category":"rushing","stats":{"YDS":"N/A"}}))
        self.assertIsNone(mod.parse_yards({"category":"passing","stats":{"YDS":"100"}}))

if __name__=="__main__":
    unittest.main()
