import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RELEASE = Path("scripts/check_release.py").read_text(encoding="utf-8")


def fixture(root, extra=""):
    (root/"scripts").mkdir()
    (root/".github/workflows").mkdir(parents=True)
    (root/"scripts/check_release.py").write_text(RELEASE, encoding="utf-8")
    (root/"index.html").write_text("<html>safe homepage</html>", encoding="utf-8")
    (root/"legacy-demo.html").write_text(
        "<html>DEMO • NO LIVE ODDS; Send to FanDuel — not connected</html>",
        encoding="utf-8")
    (root/".github/workflows/pages.yml").write_text(
        "          cp index.html _site/index.html\n"
        "          cp legacy-demo.html _site/legacy-demo.html\n"+extra,
        encoding="utf-8")


def run(root):
    return subprocess.run([sys.executable,str(root/"scripts/check_release.py")],
                          cwd=root,capture_output=True,text=True)


class ReleaseAllowlistSecurityTests(unittest.TestCase):
    def test_safe_published_pages_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            fixture(root)
            self.assertEqual(run(root).returncode,0)

    def test_legacy_browser_key_terminal_must_not_publish(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            fixture(root,"          cp nfl-edge-terminal.html _site/nfl-edge-terminal.html\n")
            (root/"nfl-edge-terminal.html").write_text("<html>legacy</html>")
            result=run(root)
            self.assertNotEqual(result.returncode,0)
            self.assertIn("Legacy browser-key terminal",result.stdout)

    def test_any_published_html_with_browser_api_call_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            fixture(root,"          cp research.html _site/research.html\n")
            (root/"research.html").write_text(
                "<html><script>fetch('https://api.the-odds-api.com/')</script></html>")
            result=run(root)
            self.assertNotEqual(result.returncode,0)
            self.assertIn("Browser-side provider API call",result.stdout)


if __name__=="__main__":
    unittest.main()
