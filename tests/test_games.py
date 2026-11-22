import importlib.util
import unittest

spec = importlib.util.spec_from_file_location("fetch_games", "scripts/fetch_games.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class GamesTests(unittest.TestCase):
    def test_normalize_scoreboard(self):
        payload = {"events": [{"id": "42", "date": "2026-11-22T18:00Z",
            "status": {"type": {"description": "Final", "state": "post"}},
            "competitions": [{"competitors": [
                {"homeAway": "home", "team": {"displayName": "Home", "abbreviation": "H"}, "score": "21"},
                {"homeAway": "away", "team": {"displayName": "Away", "abbreviation": "A"}, "score": "14"}]}]}]}
        games = mod.normalize(payload)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["home"]["score"], "21")
        self.assertEqual(games[0]["away"]["name"], "Away")
        self.assertEqual(games[0]["state"], "post")

    def test_incomplete_games_ignored(self):
        self.assertEqual(mod.normalize({"events": [{"competitions": [{"competitors": []}]}]}), [])
        self.assertEqual(mod.normalize({}), [])

if __name__ == "__main__":
    unittest.main()
