import re
import unittest
from pathlib import Path

WORKFLOW=Path(".github/workflows/pages.yml").read_text()


def cache_key(step):
    pattern=r"- name: "+re.escape(step)+r"\n(?:(?!      - name:).)*?\n\s+key: ([^\s]+)"
    match=re.search(pattern,WORKFLOW,re.S)
    if not match:
        raise AssertionError("Missing cache key for "+step)
    return match.group(1).strip()


class CacheKeyConsistencyTests(unittest.TestCase):
    def test_2025_archive_restore_and_save_keys_match(self):
        self.assertEqual(cache_key("Restore cached 2025 NFL season archive"),
                         cache_key("Cache usable 2025 archive for future deployments"))

    def test_2024_archive_restore_and_save_keys_match(self):
        self.assertEqual(cache_key("Restore cached 2024 NFL season archive"),
                         cache_key("Cache usable 2024 archive for future deployments"))

    def test_daily_history_restore_and_save_keys_match(self):
        self.assertEqual(cache_key("Restore unmerged daily historical NFL sample"),
                         cache_key("Cache only the raw, unmerged daily historical sample"))


if __name__=="__main__":
    unittest.main()
