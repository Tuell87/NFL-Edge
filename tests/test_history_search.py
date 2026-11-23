import importlib.util
import unittest

spec=importlib.util.spec_from_file_location("history_search","scripts/build_history_search.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(event,day,player="p1",category="rushing"):
    return {"event_id":event,"game_date":f"2026-11-{day:02d}T19:00:00Z",
            "player_id":player,"player":"Example Player","team":"Example Team",
            "category":category,"stats":{"YDS":str(day),"ATT":"10"}}


class MobileHistorySearchTests(unittest.TestCase):
    def test_keeps_only_latest_eight_per_player_category(self):
        source={"status":"ok","games":12,"rows":[row(f"g{i}",i) for i in range(1,13)]}
        result=mod.build(source)
        self.assertEqual(result["total_history_rows"],12)
        self.assertEqual(result["searchable_rows"],8)
        self.assertEqual([r["event_id"] for r in result["rows"]],
                         [f"g{i}" for i in range(12,4,-1)])

    def test_separates_player_and_category_and_deduplicates_events(self):
        source={"status":"ok","rows":[row("g1",1),row("g1",1),
                                          row("g1",1,category="receiving"),
                                          row("g1",1,player="p2")]}
        result=mod.build(source)
        self.assertEqual(result["searchable_rows"],3)
        self.assertEqual(result["total_history_rows"],4)

    def test_invalid_rows_do_not_produce_fake_history(self):
        result=mod.build({"status":"fetch_failed","rows":[{},{"player_id":"p"}]})
        self.assertEqual(result["status"],"insufficient_data")
        self.assertEqual(result["rows"],[])


if __name__=="__main__":
    unittest.main()
