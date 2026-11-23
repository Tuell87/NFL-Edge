import importlib.util
import unittest
from datetime import datetime, timezone
spec=importlib.util.spec_from_file_location("fetch_history","scripts/fetch_history.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class HistoryTests(unittest.TestCase):
    def test_prior_completed_events_deduplicated(self):
        def fetch(url):
            return {"events":[{"id":"123","date":"2026-11-01T20:00:00Z","status":{"type":{"state":"post"}}},{"id":"999","status":{"type":{"state":"in"}}}]}
        events=mod.recent_completed_events(datetime(2026,11,22,tzinfo=timezone.utc),fetch)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["id"],"123")

    def test_queries_nfl_game_days_not_run_weekday(self):
        from urllib.parse import parse_qs, urlparse
        requested = []
        def fetch(url):
            day = parse_qs(urlparse(url).query)["dates"][0]
            requested.append(day)
            return {"events": []}
        mod.recent_completed_events(datetime(2026, 11, 22, tzinfo=timezone.utc), fetch)
        self.assertEqual(len(requested), 126)
        self.assertIn("20261112", requested)  # Thursday before prior Sunday
        self.assertIn("20261114", requested)  # Saturday before prior Sunday
        self.assertIn("20261113", requested)  # Friday before prior Sunday
        self.assertIn("20261115", requested)  # Previous Sunday
        self.assertIn("20261116", requested)  # Monday after Sunday
        self.assertNotIn("20261122", requested)  # Never sample incomplete Sunday

    def test_multiple_game_days_and_dedup(self):
        def fetch(url):
            return {"events": [{"id": "1", "date": "2026-11-15T20:00:00Z", "status": {"type": {"state": "post"}}},
                               {"id": "2", "date": "2026-11-16T20:00:00Z", "status": {"type": {"state": "post"}}}]}
        events = mod.recent_completed_events(datetime(2026, 11, 22, tzinfo=timezone.utc), fetch)
        self.assertEqual({e["id"] for e in events}, {"1", "2"})

    def test_future_dated_post_events_are_excluded(self):
        def fetch(url):
            return {"events":[{"id":"future","date":"2026-12-01T20:00:00Z","status":{"type":{"state":"post"}}}]}
        events=mod.recent_completed_events(datetime(2026,11,22,tzinfo=timezone.utc),fetch)
        self.assertEqual(events,[])

    def test_recent_games_have_priority(self):
        def fetch(url):
            return {"events":[
                {"id":"old","date":"2026-09-01T20:00:00Z","status":{"type":{"state":"post"}}},
                {"id":"new","date":"2026-11-15T20:00:00Z","status":{"type":{"state":"post"}}}]}
        events=mod.recent_completed_events(datetime(2026,11,22,tzinfo=timezone.utc),fetch)
        self.assertEqual([event["id"] for event in events],["new","old"])

    def test_summary_failure_skipped(self):
        rows,games=mod.assemble([{"id":"123"}],lambda url: (_ for _ in ()).throw(RuntimeError("unavailable")))
        self.assertEqual(rows,[])
        self.assertEqual(games,0)

    def test_scoreboard_failures_are_counted(self):
        diagnostics={}
        def fetch(url):
            if "dates=20261115" in url:
                raise RuntimeError("network unavailable")
            return {"events":[]}
        events=mod.recent_completed_events(datetime(2026,11,22,tzinfo=timezone.utc),fetch,diagnostics)
        self.assertEqual(events,[])
        self.assertEqual(diagnostics["scoreboard_days_attempted"],126)
        self.assertEqual(diagnostics["scoreboard_days_failed"],1)
        self.assertFalse(diagnostics["event_cap_reached"])
    def test_row_limit_does_not_publish_partial_game(self):
        original_extract=mod.players.extract
        original_limit=mod.MAX_ROWS
        try:
            mod.MAX_ROWS=5
            mod.players.extract=lambda event,summary:[{"event_id":event["id"],"player_id":str(i)} for i in range(3)]
            events=[{"id":"older","date":"2026-09-01"},{"id":"newer","date":"2026-11-01"}]
            diagnostics={}
            rows,games=mod.assemble(events,lambda url:{},diagnostics)
            self.assertEqual(games,1)
            self.assertEqual(len(rows),3)
            self.assertEqual({r["event_id"] for r in rows},{"newer"})
            self.assertTrue(diagnostics["row_limit_reached"])
            self.assertEqual(diagnostics["summaries_attempted"],2)
            self.assertEqual(diagnostics["summaries_without_usable_rows"],0)
        finally:
            mod.MAX_ROWS=original_limit
            mod.players.extract=original_extract
    def test_empty_history(self):
        self.assertEqual(mod.recent_completed_events(datetime(2026,11,22,tzinfo=timezone.utc),lambda url: {}),[])

if __name__=="__main__":
    unittest.main()
