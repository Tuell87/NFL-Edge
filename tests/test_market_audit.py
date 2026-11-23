import importlib.util
import unittest
from datetime import datetime, timezone
spec=importlib.util.spec_from_file_location("audit","scripts/build_market_audit.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NOW=datetime(2026,11,22,19,tzinfo=timezone.utc)
def fixtures():
    history={"status":"ok","checked_at":"2026-11-22T18:00:00Z","rows":[
        {"event_id":str(i),"game_date":f"2026-09-{i+1:02d}T20:00:00Z","player":"Sample Runner","player_id":"player-1",
         "category":"rushing","stats":{"YDS":str(40+i)}} for i in range(6)]}
    odds={"status":"ok","updated_at":"2026-11-22T18:30:00Z","markets":[
        {"market":"player_rush_yds","side":"Over","line":44.5,"player":"Sample Runner",
         "odds":-110,"commence_time":"2026-11-29T18:00:00Z","bookmaker_updated":"2026-11-22T18:00:00Z"}]}
    matches=[{"player":"Sample Runner","market":"player_rush_yds","game_start":"2026-11-29T18:00:00+00:00",
              "opponent":"Opponent","injury_status":"unverified"}]
    return history,odds,matches
class AuditTests(unittest.TestCase):
    def test_market_line_joins_but_no_pick(self):
        result=mod.build(*fixtures(),NOW)
        self.assertEqual(result["status"],"ok")
        self.assertEqual(result["rows"][0]["prior_games"],6)
        self.assertFalse(result["rows"][0]["recommended"])
        self.assertFalse(result["rows"][0]["prediction_ready"])
        self.assertEqual(result["rows"][0]["active_roster"],"unverified")
    def test_stale_feed_is_blocked(self):
        h,o,m=fixtures()
        o["updated_at"]="2026-11-20T18:30:00Z"
        self.assertEqual(mod.build(h,o,m,NOW)["rows"],[])
    def test_duplicate_market_is_blocked(self):
        h,o,m=fixtures()
        o["markets"].append(dict(o["markets"][0]))
        self.assertEqual(mod.build(h,o,m,NOW)["rows"],[])
    def test_no_matchup_no_prediction(self):
        h,o,m=fixtures()
        self.assertEqual(mod.build(h,o,[],NOW)["rows"],[])
    def test_no_future_games(self):
        h,o,m=fixtures()
        o["markets"][0]["commence_time"]="2026-11-21T18:00:00Z"
        self.assertEqual(mod.build(h,o,m,NOW)["rows"],[])
    def test_same_name_distinct_ids_are_rejected(self):
        h,o,m=fixtures()
        h["rows"].append({**h["rows"][0],"player_id":"player-2","event_id":"different"})
        self.assertEqual(mod.build(h,o,m,NOW)["rows"],[])
    def test_minimum_five_prior_games(self):
        h,o,m=fixtures()
        h["rows"]=h["rows"][:4]
        self.assertEqual(mod.build(h,o,m,NOW)["rows"],[])
if __name__=="__main__":
    unittest.main()
