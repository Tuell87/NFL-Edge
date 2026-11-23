import importlib.util
import unittest
from datetime import datetime,timezone
spec=importlib.util.spec_from_file_location("odds","scripts/fetch_odds.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class UpcomingOddsTests(unittest.TestCase):
    def test_nearest_future_events_only(self):
        now=datetime(2026,11,22,19,tzinfo=timezone.utc)
        events=[{"id":"late","commence_time":"2026-12-01T18:00:00Z"},
                {"id":"past","commence_time":"2026-11-20T18:00:00Z"},
                {"id":"soon","commence_time":"2026-11-23T18:00:00Z"},
                {"id":"next","commence_time":"2026-11-25T18:00:00Z"}]
        self.assertEqual([x["id"] for x in mod.upcoming_events(events,now)],["soon","next"])
    def test_invalid_and_naive_dates_rejected(self):
        now=datetime(2026,11,22,19,tzinfo=timezone.utc)
        self.assertEqual(mod.upcoming_events([{"id":"x","commence_time":"bad"},
                    {"id":"y","commence_time":"2026-12-01T18:00:00"}],now),[])
    def test_orders_by_instant_and_ignores_duplicate_events(self):
        now = datetime(2026, 11, 22, tzinfo=timezone.utc)
        events = [
            {"id": "later", "commence_time": "2026-11-23T01:00:00-05:00"},
            {"id": "early", "commence_time": "2026-11-23T04:00:00Z"},
            {"id": "early", "commence_time": "2026-11-23T04:00:00Z"},
        ]
        self.assertEqual([event["id"] for event in mod.upcoming_events(events, now)], ["early", "later"])

if __name__=="__main__":
    unittest.main()
