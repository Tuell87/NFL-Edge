#!/usr/bin/env python3
"""Fetch a bounded NFL FanDuel sample for a static site. Never publish credentials."""
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
OUTPUT = Path("data/odds.json")
MARKETS = "player_anytime_td,player_reception_yds,player_rush_yds"
MAX_EVENTS = 2


def request(path, key, **params):
    query = urlencode({"apiKey": key, **params})
    with urlopen(Request(f"{BASE}{path}?{query}", headers={"Accept": "application/json"}), timeout=25) as response:
        return json.load(response)


def normalize(events, boards):
    results = []
    for event, board in zip(events, boards):
        for bookmaker in board.get("bookmakers") or []:
            if bookmaker.get("key") != "fanduel":
                continue
            for market in bookmaker.get("markets") or []:
                for outcome in market.get("outcomes") or []:
                    price = outcome.get("price")
                    if (type(price) not in (int, float) or not 100 <= abs(price) <= 2**53 - 1
                            or not math.isfinite(price) or price != int(price)):
                        continue
                    line = outcome.get("point")
                    if line is not None and (type(line) not in (int, float) or not -(2**53 - 1) <= line <= 2**53 - 1):
                        continue
                    results.append({
                        "event": f"{event.get('away_team', '')} @ {event.get('home_team', '')}",
                        "commence_time": event.get("commence_time"),
                        "market": market.get("key"),
                        "player": outcome.get("description", ""),
                        "side": outcome.get("name", ""),
                        "line": line,
                        "odds": int(price),
                        # The event-odds endpoint reports freshness per market.
                        "bookmaker_updated": market.get("last_update"),
                    })
    return results


def upcoming_events(events, now):
    eligible = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        try:
            start = datetime.fromisoformat(str(event.get("commence_time", "")).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if start.tzinfo is not None and start > now and isinstance(event.get("id"), str) and event["id"]:
            previous = eligible.get(event["id"])
            if previous is None or start < previous[0]:
                eligible[event["id"]] = (start, event)
    return [event for _, event in sorted(eligible.values(), key=lambda entry: entry[0])[:MAX_EVENTS]]


def collect(key, now):
    listing = request("/events", key)
    if not isinstance(listing, list):
        raise ValueError("Invalid odds event listing")
    events = upcoming_events(listing, now)
    markets = []
    failed = 0
    for event in events:
        try:
            board = request(f"/events/{event['id']}/odds", key, regions="us",
                            bookmakers="fanduel", markets=MARKETS, oddsFormat="american")
            if not isinstance(board, dict) or board.get("id") != event["id"]:
                raise ValueError("Odds board does not match the requested event")
            markets.extend(normalize([event], [board]))
        except (OSError, ValueError, TypeError, AttributeError):
            # Network exceptions can include a request URL with credentials.
            failed += 1
    return {
        "status": "ok" if markets else "fetch_failed" if failed else "no_markets",
        "events_checked": len(events),
        "events_failed": failed,
        "markets": markets,
    }


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key:
        OUTPUT.write_text(json.dumps({"status": "not_configured", "updated_at": now, "source": "The Odds API", "markets": []}, indent=2))
        print("Odds feed not configured: publish clear status, not fake prices")
        return
    try:
        result = collect(key, datetime.now(timezone.utc))
        result.update(updated_at=now, source="The Odds API")
        OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False))
        print(f"Published {len(result['markets'])} FanDuel outcomes across "
              f"{result['events_checked']} NFL events ({result['events_failed']} failed)")
    except Exception:
        # Do not expose exception messages: URLs or service errors may contain credentials.
        OUTPUT.write_text(json.dumps({"status": "fetch_failed", "updated_at": now, "source": "The Odds API", "markets": []}, indent=2))
        print("Odds request failed; publishing failure status without leaking request details")


if __name__ == "__main__":
    main()
