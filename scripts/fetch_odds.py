#!/usr/bin/env python3
"""
Filtered NHL odds fetcher for player_points market.
Only fetches odds for players flagged in tonight's picks across the 4 books we use.

Usage:
    python scripts/fetch_odds.py --date 2026-04-27 --window pre
    python scripts/fetch_odds.py --date 2026-04-27 --window close
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

API_KEY = os.environ.get("ODDS_API_KEY")
API_URL = "https://api.the-odds-api.com/v4/sports/icehockey_nhl/odds"
BOOKS = "bet365,draftkings,fanatics,fanduel"
MARKET = "player_points"

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PICKS_FILE_TEMPLATE = "tonights_picks_{date}.json"
OUTPUT_TEMPLATE = "odds_{date}_{window}.json"


def load_target_players(date: str) -> set[str]:
    """Read tonight's picks file and extract the set of player names to filter on."""
    picks_path = DATA_DIR / PICKS_FILE_TEMPLATE.format(date=date)
    if not picks_path.exists():
        sys.exit(f"ERROR: picks file not found: {picks_path}")

    with picks_path.open() as f:
        picks = json.load(f)

    players = set()
    for p in picks.get("tier_a_cold", []):
        players.add(p["player"].strip())
    for duo in picks.get("paper_duos", []):
        players.add(duo["p1"].strip())
        players.add(duo["p2"].strip())
    return players


def fetch_odds() -> list[dict]:
    """Hit The Odds API once and return the raw games list."""
    if not API_KEY:
        sys.exit("ERROR: set ODDS_API_KEY env var")

    params = {
        "regions": "us,us2,uk",
        "markets": MARKET,
        "bookmakers": BOOKS,
        "oddsFormat": "american",
        "apiKey": API_KEY,
    }
    r = requests.get(API_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def filter_and_compact(games: list[dict], target_players: set[str]) -> list[dict]:
    """Keep only outcomes for target players. Strip everything else."""
    out = []
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for game in games:
        game_id = game.get("id")
        commence = game.get("commence_time")
        home = game.get("home_team")
        away = game.get("away_team")
        game_label = f"{away} @ {home}"

        for book in game.get("bookmakers", []):
            book_key = book.get("key")
            for market in book.get("markets", []):
                if market.get("key") != MARKET:
                    continue
                for outcome in market.get("outcomes", []):
                    player = (outcome.get("description") or "").strip()
                    if player not in target_players:
                        continue
                    out.append({
                        "player": player,
                        "side": outcome.get("name"),
                        "line": outcome.get("point"),
                        "price": outcome.get("price"),
                        "book": book_key,
                        "game": game_label,
                        "game_id": game_id,
                        "commence": commence,
                        "fetched_at": fetched_at,
                    })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--window", required=True, choices=["pre", "close"])
    args = ap.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    target_players = load_target_players(args.date)
    if not target_players:
        sys.exit("ERROR: no target players in picks file")

    print(f"Fetching odds for {len(target_players)} players, books={BOOKS}, market={MARKET}")
    games = fetch_odds()
    rows = filter_and_compact(games, target_players)

    out_path = DATA_DIR / OUTPUT_TEMPLATE.format(date=args.date, window=args.window)
    with out_path.open("w") as f:
        json.dump(rows, f, indent=1)

    size_kb = out_path.stat().st_size / 1024
    print(f"Wrote {len(rows)} rows → {out_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
