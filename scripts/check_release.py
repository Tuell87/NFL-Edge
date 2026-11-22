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
if "Send to FanDuel — not connected" not in html:
    errors.append("Unverified sportsbook transfer must be disabled")
if re.search(r'<script[^>]+src=["\']https?://', html + legacy, re.I):
    errors.append("External scripts are not allowed")
if re.search(r'api\.the-odds-api\.com', html, re.I):
    errors.append("Browser-side odds API calls are not allowed")
if re.search(r'(?i)(?:api[_-]?key|secret|token)\s*[:=]\s*["\'][A-Za-z0-9_-]{20,}', html + legacy):
    errors.append("Possible embedded credential")
for name in (".env", "credentials.json", "secrets.json"):
    if (root / name).exists():
        errors.append(f"Forbidden file: {name}")
if errors:
    print("RELEASE BLOCKED:\n - " + "\n - ".join(errors))
    sys.exit(1)
print("Static release checks passed; not a complete security audit.")
