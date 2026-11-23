import importlib.util
import unittest
from datetime import datetime, timezone

spec = importlib.util.spec_from_file_location("rosters", "scripts/fetch_rosters.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
spec2 = importlib.util.spec_from_file_location("matchups_roster", "scripts/build_matchups.py")
matchups = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(matchups)


class RosterTests(unittest.TestCase):
    def test_grouped_and_flat_roster_parsing(self):
        data = {"athletes": [{"position": "QB", "items": [{"id": "12", "displayName": "Example A"}]},
                             {"id": "13", "displayName": "Example B"}]}
        self.assertEqual([a["player_id"] for a in mod.extract(data)], ["12", "13"])

    def test_partial_fetch_failure_does_not_fabricate_roster(self):
        games = [{"home": {"name": "Team A", "abbreviation": "AAA"},
                  "away": {"name": "Team B", "abbreviation": "BBB"}}]
        def fetch(url):
            if "aaa" in url:
                return {"athletes": [{"id": "12", "displayName": "Example"}]}
            raise OSError("unavailable")
        result = mod.collect(games, fetch)
        self.assertEqual(result["teams_with_rosters"], 1)
        self.assertEqual(next(t for t in result["teams"] if t["abbreviation"] == "BBB")["status"], "fetch_failed")

    def test_roster_presence_never_verifies_game_day_active_or_injury(self):
        games = [{"id": "g", "start": "2026-12-01T20:00:00Z", "state": "pre",
                  "home": {"name": "Team A"}, "away": {"name": "Team B"}}]
        players = [{"player": "Example", "player_id": "12", "team": "Team A",
                    "market": "player_rush_yds", "games": 7}]
        rosters = {"checked_at": "2026-11-23T00:00:00Z", "teams": [{"team": "Team A", "status": "listed",
                             "athletes": [{"player_id": "12", "player": "Example"}]}]}
        rows = matchups.build(games, players, datetime(2026, 11, 23, tzinfo=timezone.utc), rosters)
        self.assertEqual(rows[0]["roster_listing"], "listed")
        self.assertEqual(rows[0]["availability"], "unverified")
        self.assertEqual(rows[0]["injury_status"], "unverified")
        self.assertFalse(rows[0]["prediction_ready"])
        self.assertIn("independent_availability_source_not_integrated", rows[0]["readiness_blockers"])

    def test_stale_roster_is_not_treated_as_current(self):
        games = [{"id": "g", "start": "2026-12-01T20:00:00Z", "state": "pre",
                  "home": {"name": "Team A"}, "away": {"name": "Team B"}}]
        players = [{"player": "Example", "player_id": "12", "team": "Team A",
                    "market": "player_rush_yds", "games": 7}]
        rosters = {"checked_at": "2026-11-01T00:00:00Z", "teams": [
            {"team": "Team A", "status": "listed", "athletes": [{"player_id": "12"}]}]}
        rows = matchups.build(games, players, datetime(2026, 11, 23, tzinfo=timezone.utc), rosters)
        self.assertEqual(rows[0]["roster_listing"], "unavailable")
    def test_missing_roster_player_is_not_called_inactive(self):
        games = [{"id": "g", "start": "2026-12-01T20:00:00Z", "state": "pre",
                  "home": {"name": "Team A"}, "away": {"name": "Team B"}}]
        players = [{"player": "Example", "player_id": "12", "team": "Team A",
                    "market": "player_rush_yds", "games": 7}]
        rosters = {"teams": [{"team": "Team A", "status": "listed",
                             "athletes": [{"player_id": "99", "player": "Other"}]}]}
        rows = matchups.build(games, players, datetime(2026, 11, 23, tzinfo=timezone.utc), rosters)
        self.assertEqual(rows[0]["roster_listing"], "not_found_in_snapshot")
        self.assertEqual(rows[0]["availability"], "unverified")


if __name__ == "__main__":
    unittest.main()
