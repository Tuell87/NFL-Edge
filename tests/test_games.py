import importlib.util
import unittest
from urllib.parse import parse_qs, urlsplit

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

    def test_scoreboard_includes_next_week_and_preserves_primary_on_failure(self):
        def event(game_id, state):
            return {"id": game_id, "status": {"type": {"state": state}},
                    "competitions": [{"competitors": [
                        {"homeAway": "home", "team": {"displayName": "Home"}},
                        {"homeAway": "away", "team": {"displayName": "Away"}},
                    ]}]}

        current = {
            "season": {"year": 2026, "type": 2}, "week": {"number": 11},
            "leagues": [{"calendar": [{"value": "2", "entries": [
                {"value": "11"}, {"value": "12"},
            ]}]}],
            "events": [event("current", "post")],
        }

        def get(url):
            if url == mod.URL:
                return current
            self.assertEqual(parse_qs(urlsplit(url).query),
                             {"dates": ["2026"], "seasontype": ["2"], "week": ["12"]})
            return {"events": [event("current", "pre"), event("upcoming", "pre"),
                               event("upcoming", "pre"), event("final", "post")]}

        games, coverage = mod.collect(get)
        self.assertEqual([(g["id"], g["state"]) for g in games],
                         [("current", "post"), ("upcoming", "pre")])
        self.assertEqual(coverage, "next_week_included")

        def unavailable(url):
            if url == mod.URL:
                return current
            raise OSError("Temporary ESPN failure")

        games, coverage = mod.collect(unavailable)
        self.assertEqual([g["id"] for g in games], ["current"])
        self.assertEqual(coverage, "next_week_unavailable")

if __name__ == "__main__":
    unittest.main()
