import importlib.util
import unittest

spec=importlib.util.spec_from_file_location("observations","scripts/observations.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(event="e1",player="p1",yards="40"):
    return {"event_id":event,"player_id":player,"category":"rushing",
            "game_date":"2026-11-01","team":"A","stats":{"YDS":yards}}


class ObservationIdentityTests(unittest.TestCase):
    def test_identical_rows_collapse_to_one(self):
        rows=[row(),row(),row("e2")]
        self.assertEqual(len(mod.unique_rows(rows)),2)

    def test_conflicting_stats_exclude_entire_ambiguous_event(self):
        rows=[row(yards="30"),row(yards="90"),row("e2")]
        result=mod.unique_rows(rows)
        self.assertEqual([r["event_id"] for r in result],["e2"])

    def test_conflicting_team_excluded(self):
        a=row()
        b={**a,"team":"B"}
        self.assertEqual(mod.unique_rows([a,b]),[])

    def test_no_stable_identity_cannot_be_name_matched(self):
        a={**row(),"player_id":"","player":"Example"}
        self.assertEqual(mod.unique_rows([a]),[])


if __name__=="__main__":
    unittest.main()
