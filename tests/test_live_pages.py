import importlib.util
import json
import unittest
from urllib.parse import urlparse

spec = importlib.util.spec_from_file_location("live_pages", "scripts/check_live_pages.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def response(path, *, unsafe=False):
    if path.endswith(".html") or path == "/NFL-Edge/":
        return b"<!doctype html><html><head></head><body>ok</body></html>", "text/html"
    if path.endswith("odds.json"):
        return json.dumps({"status": "no_markets", "markets": [], "updated_at": "2026-11-23T00:00:00Z"}).encode(), "application/json"
    if path.endswith("history_search.json"):
        return json.dumps({"status": "ok", "rows": [], "total_history_rows": 0, "searchable_rows": 0}).encode(), "application/json"
    if path.endswith("research_status.json"):
        return json.dumps({"status": "research_only", "readiness_blockers": [], "prediction_ready": False}).encode(), "application/json"
    if path.endswith("opponent_seasons.json"):
        return json.dumps({"status": "insufficient_data", "tests": [], "prediction_ready": False}).encode(), "application/json"
    if path.endswith("opponent_rolling.json"):
        return json.dumps({"status": "insufficient_data", "windows": [], "prediction_ready": False}).encode(), "application/json"
    if path.endswith("opponent_holdout.json") or path.endswith("opponent_evaluation.json"):
        return json.dumps({"status": "insufficient_data", "metrics": []}).encode(), "application/json"
    if path.endswith("feed_integrity.json"):
        return json.dumps({"status": "ok", "warnings": [], "errors": []}).encode(), "application/json"
    if path.endswith("roster_quality.json"):
        return json.dumps({"teams_requested": 0, "prediction_ready": False}).encode(), "application/json"
    if path.endswith("matchups.json"):
        return json.dumps({"status": "ok", "matchups": [{"prediction_ready": False}]}).encode(), "application/json"
    if path.endswith("market_audit.json"):
        return json.dumps({"status": "ok", "rows": [{
            "prediction_ready": False, "recommended": unsafe}]}).encode(), "application/json"
    raise OSError("unexpected path")


class LiveSmokeTests(unittest.TestCase):
    def test_valid_site_can_be_checked_without_network(self):
        def get(url):
            return response(urlparse(url).path)
        self.assertEqual(mod.check("https://example.com/NFL-Edge/", get), [])

    def test_unsafe_recommendation_blocks_live_verification(self):
        def get(url):
            return response(urlparse(url).path, unsafe=True)
        self.assertTrue(any("unsafe market" in error
                            for error in mod.check("https://example.com/NFL-Edge/", get)))

    def test_old_release_is_not_mistaken_for_new_deployment(self):
        def get(url):
            path=urlparse(url).path
            if path.endswith("research_status.json"):
                return json.dumps({"status":"research_only","readiness_blockers":[],
                                   "prediction_ready":False,
                                   "release_sha":"old_commit"}).encode(), "application/json"
            return response(path)
        errors=mod.check("https://example.com/NFL-Edge/",get,expected_sha="new_commit")
        self.assertTrue(any("release SHA" in error for error in errors))
        self.assertEqual(mod.check("https://example.com/NFL-Edge/",get,
                                   expected_sha="old_commit"),[])

    def test_missing_published_page_is_reported(self):
        def get(url):
            if url.endswith("opponent-holdout.html"):
                raise OSError("404")
            return response(urlparse(url).path)
        self.assertTrue(any("opponent-holdout.html" in error
                            for error in mod.check("https://example.com/NFL-Edge/", get)))

    def test_missing_odds_page_and_malformed_odds_rows_block_verification(self):
        def get(url):
            path = urlparse(url).path
            if path.endswith("/odds.html"):
                raise OSError("404")
            if path.endswith("/odds.json"):
                return b'{"status":"ok","updated_at":null,"markets":{}}', "application/json"
            return response(path)
        errors = mod.check("https://example.com/NFL-Edge/", get)
        self.assertTrue(any(error.startswith("odds.html:") for error in errors))
        self.assertIn("data/odds.json: markets must be an array", errors)

    def test_invalid_json_is_reported(self):
        def get(url):
            if url.endswith("feed_integrity.json"):
                return b"not-json", "text/plain"
            return response(urlparse(url).path)
        self.assertTrue(any("feed_integrity.json" in error
                            for error in mod.check("https://example.com/NFL-Edge/", get)))


if __name__ == "__main__":
    unittest.main()
