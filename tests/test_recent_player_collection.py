import importlib.util
import unittest
from datetime import datetime, timezone

spec = importlib.util.spec_from_file_location("recent_players", "scripts/fetch_players.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NOW = datetime(2026, 11, 23, tzinfo=timezone.utc)


def event(identifier, date, state="post"):
    return {"id": identifier, "date": date, "status": {"type": {"state": state}}}


class RecentPlayerCollectionTests(unittest.TestCase):
    def test_newest_first_and_no_partial_game(self):
        original_extract, original_limit = mod.extract, mod.MAX_PLAYERS
        try:
            mod.MAX_PLAYERS = 5
            mod.extract = lambda e, summary: [{"event_id": e["id"], "player_id": str(i)}
                                              for i in range(3)]
            board = {"events": [event("old", "2026-11-01T20:00:00Z"),
                                event("new", "2026-11-20T20:00:00Z")]}
            result = mod.collect(board, lambda url: {}, NOW)
            self.assertEqual({r["event_id"] for r in result["players"]}, {"new"})
            self.assertEqual(result["games_with_stats"], 1)
            self.assertTrue(result["player_row_limit_reached"])
            self.assertEqual(result["games_checked"], 2)
        finally:
            mod.extract, mod.MAX_PLAYERS = original_extract, original_limit

    def test_future_in_progress_and_duplicate_events_ignored(self):
        original_extract = mod.extract
        try:
            mod.extract = lambda e, summary: [{"event_id": e["id"]}]
            board = {"events": [event("a", "2026-11-20T20:00:00Z"),
                                event("a", "2026-11-20T20:00:00Z"),
                                event("future", "2026-12-01T20:00:00Z"),
                                event("live", "2026-11-20T20:00:00Z", "in")]}
            result = mod.collect(board, lambda url: {}, NOW)
            self.assertEqual(result["completed_events_discovered"], 1)
            self.assertEqual(result["games_checked"], 1)
        finally:
            mod.extract = original_extract

    def test_summary_failures_reported_without_fabricated_rows(self):
        board = {"events": [event("a", "2026-11-20T20:00:00Z")]}
        result = mod.collect(board, lambda url: (_ for _ in ()).throw(OSError("offline")), NOW)
        self.assertEqual(result["status"], "no_stats")
        self.assertEqual(result["summary_failures_or_empty"], 1)
        self.assertEqual(result["players"], [])


if __name__ == "__main__":
    unittest.main()
