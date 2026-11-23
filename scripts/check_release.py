"""Static release gate; does not replace a security audit."""
from pathlib import Path
import re
import sys
root = Path(__file__).resolve().parents[1]
html = (root / "index.html").read_text(encoding="utf-8")
legacy = (root / "legacy-demo.html").read_text(encoding="utf-8")
errors = []
if "DEMO • NO LIVE ODDS" not in legacy:
    errors.append("Missing demo disclaimer")
if "Send to FanDuel — not connected" not in legacy:
    errors.append("Unverified sportsbook transfer must be disabled")
if re.search(r'<script[^>]+src=["\']https?://', html + legacy, re.I):
    errors.append("External scripts are not allowed")
if re.search(r'api\.the-odds-api\.com', html, re.I):
    errors.append("Browser-side odds API calls are not allowed")
if re.search(r'(?i)(?:api[_-]?key|secret|token)\s*[:=]\s*["\'][A-Za-z0-9_-]{20,}', html + legacy):
    errors.append("Possible embedded credential")
# Scan every HTML page that the Pages allowlist actually publishes.
# The older 134 KB terminal is intentionally excluded: it stores a browser
# API key in localStorage and sends direct provider requests.
workflow = (root / ".github/workflows/pages.yml").read_text(encoding="utf-8")
published = re.findall(r"^\\s*cp\\s+([\\w.-]+\\.html)\\s+_site/[\\w.-]+\\.html\\s*$",
                       workflow, re.M)
if not published:
    errors.append("No published HTML allowlist detected")
if "nfl-edge-terminal.html" in published:
    errors.append("Legacy browser-key terminal must never be published")
for name in published:
    page = root / name
    if not page.is_file():
        errors.append(f"Missing published HTML: {name}")
        continue
    body = page.read_text(encoding="utf-8")
    if re.search(r"api\\.the-odds-api\\.com|apiKey\\s*=", body, re.I):
        errors.append(f"Browser-side provider API call in published page: {name}")
    if re.search(r"<script[^>]+src=[\\\"']https?://", body, re.I):
        errors.append(f"External JavaScript in published page: {name}")
for name in (".env", "credentials.json", "secrets.json"):
    if (root / name).exists():
        errors.append(f"Forbidden file: {name}")
if errors:
    print("RELEASE BLOCKED:\n - " + "\n - ".join(errors))
    sys.exit(1)
print("Static release checks passed; not a complete security audit.")
