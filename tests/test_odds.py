import importlib.util
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("fetch_odds", "scripts/fetch_odds.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class OddsCollectorTests(unittest.TestCase):
    def test_normalizes_only_fanduel(self):
        events = [{"home_team": "Home", "away_team": "Away", "commence_time": "2026-11-22T20:00:00Z"}]
        boards = [{"bookmakers": [
            {"key": "other", "markets": [{"key": "player_anytime_td", "outcomes": [{"price": 100}]}]},
            {"key": "fanduel", "last_update": "2026-11-22T19:00:00Z", "markets": [
                {"key": "player_anytime_td", "outcomes": [{"name": "Yes", "description": "Player A", "price": 135}]}]}]}]
        rows = mod.normalize(events, boards)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["player"], "Player A")
        self.assertEqual(rows[0]["odds"], 135)
        self.assertEqual(rows[0]["event"], "Away @ Home")

    def test_uses_market_timestamp_and_preserves_unknown_freshness(self):
        events = [{"home_team": "Home", "away_team": "Away"}]
        boards = [{"bookmakers": [{
            "key": "fanduel",
            "last_update": "2026-11-22T18:00:00Z",
            "markets": [
                {"key": "player_reception_yds", "last_update": "2026-11-22T19:00:00Z",
                 "outcomes": [{"price": -110}, {"price": -105}]},
                {"key": "player_rush_yds", "last_update": "2026-11-22T19:10:00Z",
                 "outcomes": [{"price": -115}]},
                {"key": "player_anytime_td", "outcomes": [{"price": 135}]},
            ],
        }]}]
        self.assertEqual(
            [row["bookmaker_updated"] for row in mod.normalize(events, boards)],
            ["2026-11-22T19:00:00Z", "2026-11-22T19:00:00Z", "2026-11-22T19:10:00Z", None],
        )

    def test_missing_key_publishes_not_configured_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(mod, "OUTPUT", Path(tmp) / "odds.json"):
                with patch.dict(os.environ, {"ODDS_API_KEY": ""}):
                    with patch.object(mod, "request", side_effect=AssertionError("network should not be called")):
                        mod.main()
                body = json.loads((Path(tmp) / "odds.json").read_text())
                self.assertEqual(body["status"], "not_configured")
                self.assertEqual(body["markets"], [])

    def test_bad_prices_are_excluded(self):
        events = [{"home_team": "A", "away_team": "B"}]
        boards = [{"bookmakers": [{"key": "fanduel", "markets": [
            {"key": "player_anytime_td", "outcomes": [{"price": "not an odd"}, {"price": True}]}]}]}]
        self.assertEqual(mod.normalize(events, boards), [])


    def test_preserves_valid_event_when_other_event_fails_or_does_not_match(self):
        now = datetime(2026, 11, 22, tzinfo=timezone.utc)
        events = [
            {"id": key, "away_team": "Away", "home_team": "Home",
             "commence_time": f"2026-11-{day}T18:00:00Z"}
            for key, day in [("first", 23), ("second", 24)]
        ]
        board = {"id": "second", "bookmakers": [{"key": "fanduel", "markets": [
            {"key": "player_anytime_td", "outcomes": [
                {"price": 150, "description": "Player B"},
                {"price": 150.5, "description": "Invalid price"},
                {"price": 150, "point": float("nan"), "description": "Invalid line"},
            ]},
        ]}]}
        for bad in (OSError("failed request"), {"id": "wrong", "bookmakers": board["bookmakers"]}):
            with self.subTest(bad=type(bad)), patch.object(mod, "request", side_effect=[events, bad, board]):
                result = mod.collect("test-key", now)
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["events_failed"], 1)
                self.assertEqual([row["player"] for row in result["markets"]], ["Player B"])


if __name__ == "__main__":
    unittest.main()
