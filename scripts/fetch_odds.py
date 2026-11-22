#!/usr/bin/env python3
"""Fetch a bounded NFL FanDuel sample for a static site. Never publish credentials."""
import json
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
        for bookmaker in board.get("bookmakers", []):
            if bookmaker.get("key") != "fanduel":
                continue
            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    price = outcome.get("price")
                    if not isinstance(price, (int, float)) or isinstance(price, bool):
                        continue
                    results.append({
                        "event": f"{event.get('away_team', '')} @ {event.get('home_team', '')}",
                        "commence_time": event.get("commence_time"),
                        "market": market.get("key"),
                        "player": outcome.get("description", ""),
                        "side": outcome.get("name", ""),
                        "line": outcome.get("point"),
                        "odds": price,
                        "bookmaker_updated": bookmaker.get("last_update"),
                    })
    return results


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key:
        OUTPUT.write_text(json.dumps({"status": "not_configured", "updated_at": now, "source": "The Odds API", "markets": []}, indent=2))
        print("Odds feed not configured: publish clear status, not fake prices")
        return
    try:
        events = request("/events", key)[:MAX_EVENTS]
        boards = [request(f"/events/{event['id']}/odds", key, regions="us", bookmakers="fanduel", markets=MARKETS, oddsFormat="american") for event in events]
        markets = normalize(events, boards)
        result = {"status": "ok" if markets else "no_markets", "updated_at": now, "source": "The Odds API", "events_checked": len(events), "markets": markets}
        OUTPUT.write_text(json.dumps(result, indent=2))
        print(f"Published {len(markets)} FanDuel outcomes across {len(events)} NFL events")
    except Exception as exc:
        # Do not expose exception messages: URLs or service errors may contain credentials.
        OUTPUT.write_text(json.dumps({"status": "fetch_failed", "updated_at": now, "source": "The Odds API", "markets": []}, indent=2))
        print("Odds request failed; publishing failure status without leaking request details")


if __name__ == "__main__":
    main()
