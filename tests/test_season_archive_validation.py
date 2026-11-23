import importlib.util
import unittest

spec = importlib.util.spec_from_file_location("archive_check", "scripts/check_season_archive.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def archive(games=205, wrong=False):
    rows = [{"event_id": str(i), "game_date": f"2025-09-{i % 20 + 1:02d}",
             "player_id": str(i)} for i in range(games)]
    if wrong:
        rows[-1]["game_date"] = "2026-11-22"
    return {"status": "ok", "season": 2025, "games": games, "rows": rows,
            "scoreboard_days_attempted": 161, "scoreboard_days_failed": 0}


class ArchiveValidationTests(unittest.TestCase):
    def test_good_archive_cacheable(self):
        result = mod.inspect(archive())
        self.assertTrue(result["safe_to_merge"])
        self.assertTrue(result["cacheable"])

    def test_2024_archive_validated_against_2024_season(self):
        data = archive()
        data["season"] = 2024
        for row in data["rows"]:
            row["game_date"] = row["game_date"].replace("2025-", "2024-")
        self.assertTrue(mod.inspect(data, expected_season=2024)["cacheable"])
        self.assertFalse(mod.inspect(data, expected_season=2025)["safe_to_merge"])

    def test_sparse_archive_may_merge_but_is_not_cached(self):
        result = mod.inspect(archive(20))
        self.assertTrue(result["safe_to_merge"])
        self.assertFalse(result["cacheable"])

    def test_wrong_season_rejected(self):
        result = mod.inspect(archive(wrong=True))
        self.assertFalse(result["safe_to_merge"])
        self.assertFalse(result["cacheable"])

    def test_mismatched_event_count_rejected(self):
        data = archive()
        data["games"] += 1
        self.assertFalse(mod.inspect(data)["safe_to_merge"])

    def test_near_full_285_game_archive_is_cached_despite_failed_empty_dates(self):
        data=archive(285)
        data["scoreboard_days_failed"]=30
        result=mod.inspect(data)
        self.assertTrue(result["safe_to_merge"])
        self.assertTrue(result["near_full_season_event_count"])
        self.assertTrue(result["cacheable"])

    def test_failed_scoreboard_days_block_cache(self):
        data = archive()
        data["scoreboard_days_failed"] = 30
        self.assertTrue(mod.inspect(data)["safe_to_merge"])
        self.assertFalse(mod.inspect(data)["cacheable"])


if __name__ == "__main__":
    unittest.main()
