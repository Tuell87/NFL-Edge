#!/usr/bin/env python3
"""Check the publicly deployed GitHub Pages site after a successful upload.

Do not equate passing repository CI with a successful live deployment.
Validate actual HTTP responses, JSON structure and fail-closed recommendation
flags. No odds API secrets are used.
"""
import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

DEFAULT_BASE = "https://tuell87.github.io/NFL-Edge/"
PAGES = ("", "dashboard.html", "opponent-holdout.html", "opponent-evaluation.html", "opponent-rolling.html", "opponent-seasons.html",
         "feed-integrity.html", "roster-quality.html")
DATA = {
    "data/opponent_holdout.json": ("metrics", "status"),
    "data/opponent_rolling.json": ("windows", "prediction_ready", "status"),
    "data/opponent_seasons.json": ("tests", "prediction_ready", "status"),
    "data/research_status.json": ("readiness_blockers", "prediction_ready", "status"),
    "data/opponent_evaluation.json": ("metrics", "status"),
    "data/feed_integrity.json": ("warnings", "errors", "status"),
    "data/roster_quality.json": ("teams_requested", "prediction_ready"),
    "data/matchups.json": ("matchups", "status"),
    "data/market_audit.json": ("rows", "status"),
}


def fetch(url, timeout=15):
    with urlopen(Request(url, headers={"User-Agent": "NFL-Edge-Deployment-Health/1.0",
                                      "Cache-Control": "no-cache"}), timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", "")


def check(base=DEFAULT_BASE, get=fetch, expected_sha=None):
    errors = []
    base = base.rstrip("/") + "/"
    for path in PAGES:
        url = urljoin(base, path)
        try:
            content, mime = get(url)
            if not content or b"<html" not in content[:1000].lower():
                errors.append(f"{path or 'index.html'}: HTML missing")
        except (OSError, HTTPError, URLError, TimeoutError, ValueError) as exc:
            errors.append(f"{path or 'index.html'}: {type(exc).__name__}")
    for path, required in DATA.items():
        try:
            content, mime = get(urljoin(base, path))
            data = json.loads(content)
            if not isinstance(data, dict) or any(k not in data for k in required):
                errors.append(f"{path}: invalid JSON contract")
                continue
            if path.endswith("research_status.json") and expected_sha and data.get("release_sha") != expected_sha:
                errors.append(f"{path}: deployed release SHA does not match this workflow run")
            if path.endswith("research_status.json") and data["prediction_ready"] is not False:
                errors.append(f"{path}: research cannot be prediction ready")
            if path.endswith("roster_quality.json") and data["prediction_ready"] is not False:
                errors.append(f"{path}: must not mark predictions ready")
            if path.endswith("feed_integrity.json") and data.get("errors"):
                errors.append(f"{path}: integrity errors reported")
            if path.endswith("matchups.json"):
                if any(not isinstance(row, dict) or row.get("prediction_ready") is not False
                       for row in data["matchups"]):
                    errors.append(f"{path}: unsafe matchup readiness")
            if path.endswith("market_audit.json"):
                if any(not isinstance(row, dict) or row.get("prediction_ready") is not False
                       or row.get("recommended") is not False for row in data["rows"]):
                    errors.append(f"{path}: unsafe market recommendation")
        except (OSError, HTTPError, URLError, TimeoutError, ValueError, TypeError) as exc:
            errors.append(f"{path}: {type(exc).__name__}")
    return errors


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE
    attempts = 8
    for attempt in range(1, attempts + 1):
        errors = check(base, expected_sha=os.environ.get("GITHUB_SHA"))
        if not errors:
            print("PASS: live Pages HTML, data contracts and recommendation safety verified")
            return
        print(f"Live smoke attempt {attempt}/{attempts}:", "; ".join(errors))
        if attempt < attempts:
            time.sleep(15)
    raise SystemExit("FAIL: deployed Pages site could not be verified")


if __name__ == "__main__":
    main()
