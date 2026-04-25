#!/usr/bin/env python3
"""
NHL Linemate Duo Correlation Tracker — TONIGHT.PY
One-command nightly pipeline

Usage:
    py tonight.py               # lineups + verify only
    py tonight.py --advanced    # lineups + verify + goalies + advanced metrics
"""

import argparse
import subprocess
import sys
from datetime import datetime


def get_todays_date():
    return datetime.now().strftime("%Y-%m-%d")


def get_playing_teams():
    date = get_todays_date()
    print(f"\n🏒 NHL Linemate Duo Tracker — {date}\n")
    print("Enter tonight's playing teams (comma-separated, e.g. EDM,ANA,VGK,UTA)")
    teams_input = input("> ").strip()

    if teams_input:
        teams = [t.strip().upper() for t in teams_input.split(",")]
    else:
        teams = ["EDM", "ANA", "VGK", "UTA"]

    return teams, date


def run_command(cmd):
    print(f"🚀 Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print("STDERR:", result.stderr.strip())
        print("✅ Done\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Nightly NHL Linemate pipeline")
    parser.add_argument(
        "--advanced", action="store_true",
        help="Also fetch goalies and advanced metrics (GSAx, Fenwick, xGF%%)"
    )
    args = parser.parse_args()

    teams, date = get_playing_teams()
    print(f"📅 Processing for {date}\n")

    # Always run: lineups + verify
    run_command(f"py scripts\\fetch_lineups_nhl.py --date {date}")
    run_command(f"py scripts\\verify_players.py --date {date} --elite-only")

    # Optional: goalies + advanced metrics (required for full STEP 3 pre-flight)
    if args.advanced:
        run_command(f"py scripts\\fetch_goalies.py --date {date}")
        run_command(f"py scripts\\fetch_advanced_metrics.py --date {date}")

    print("🎉 Pipeline complete!")
    print("\nNext steps — upload these files to your Claude Project:")
    print(f"   lineups_{date}.json")
    print(f"   verified_{date}.json")
    if args.advanced:
        print(f"   goalies_{date}.json")
        print(f"   advanced_metrics_{date}.json")
    print("\nThen paste the latest nightly prompt (Quick Fix v5).")
    print("You're ready! 🔥")


if __name__ == "__main__":
    main()
