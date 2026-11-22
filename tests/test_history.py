import importlib.util
import unittest
from datetime import datetime, timezone
spec=importlib.util.spec_from_file_location("fetch_history","scripts/fetch_history.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class HistoryTests(unittest.TestCase):
    def test_prior_completed_events_deduplicated(self):
        def fetch(url):
            return {"events":[{"id":"123","date":"2026-11-01","status":{"type":{"state":"post"}}},{"id":"999","status":{"type":{"state":"in"}}}]}
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
        self.assertEqual(len(requested), 18)
        self.assertIn("20261112", requested)  # Thursday before prior Sunday
        self.assertIn("20261115", requested)  # Previous Sunday
        self.assertIn("20261116", requested)  # Monday after Sunday
        self.assertNotIn("20261122", requested)  # Never sample incomplete Sunday

    def test_multiple_game_days_and_dedup(self):
        def fetch(url):
            return {"events": [{"id": "1", "date": "2026-11-15", "status": {"type": {"state": "post"}}},
                               {"id": "2", "date": "2026-11-16", "status": {"type": {"state": "post"}}}]}
        events = mod.recent_completed_events(datetime(2026, 11, 22, tzinfo=timezone.utc), fetch)
        self.assertEqual({e["id"] for e in events}, {"1", "2"})

    def test_summary_failure_skipped(self):
        rows,games=mod.assemble([{"id":"123"}],lambda url: (_ for _ in ()).throw(RuntimeError("unavailable")))
        self.assertEqual(rows,[])
        self.assertEqual(games,0)

    def test_empty_history(self):
        self.assertEqual(mod.recent_completed_events(datetime(2026,11,22,tzinfo=timezone.utc),lambda url: {}),[])

if __name__=="__main__":
    unittest.main()
