#!/usr/bin/env python3
"""
Writes data/tonights_picks_<date>.json in the shape expected by fetch_odds.py.

Two ways to use:

1. Import and call from tonight.py
2. Run standalone for testing
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def write_picks(date: str, tier_a: list, duos: list) -> Path:
    """Write the picks file for a given date."""
    DATA_DIR.mkdir(exist_ok=True)
    payload = {
        "date": date,
        "tier_a_cold": tier_a,
        "paper_duos": duos,
    }
    out_path = DATA_DIR / f"tonights_picks_{date}.json"
    with out_path.open("w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote picks file -> {out_path}")
    return out_path


def _example(date: str) -> None:
    """Test mode: writes a small sample picks file."""
    tier_a = [
        {"player": "Brent Burns", "team": "CAR"},
        {"player": "Jordan Martinook", "team": "CAR"},
    ]
    duos = [
        {"p1": "Sebastian Aho", "p2": "Seth Jarvis", "tier": "ELITE"},
    ]
    write_picks(date=date, tier_a=tier_a, duos=duos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()
    _example(args.date)


if __name__ == "__main__":
    main()
