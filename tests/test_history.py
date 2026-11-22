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

    def test_summary_failure_skipped(self):
        rows,games=mod.assemble([{"id":"123"}],lambda url: (_ for _ in ()).throw(RuntimeError("unavailable")))
        self.assertEqual(rows,[])
        self.assertEqual(games,0)

    def test_empty_history(self):
        self.assertEqual(mod.recent_completed_events(datetime(2026,11,22,tzinfo=timezone.utc),lambda url: {}),[])

if __name__=="__main__":
    unittest.main()
