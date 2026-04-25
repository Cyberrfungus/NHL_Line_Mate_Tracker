#!/usr/bin/env python3
"""
NHL Linemate Duo Correlation Tracker — TONIGHT.PY
One-command nightly pipeline

Usage:
    py tonight.py                   # pre-game: lineups + verify
    py tonight.py --advanced        # pre-game: lineups + verify + goalies + advanced metrics
    py tonight.py --post-game       # post-game: fetch chains + auto-score vs predictions
    py tonight.py --post-game --date 2026-04-21   # score a specific past date
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta


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


def run_pre_game(date, advanced):
    """Fetch lineups, verify players, and optionally pull advanced signals."""
    run_command(f"py scripts\\fetch_lineups_nhl.py --date {date}")
    run_command(f"py scripts\\verify_players.py --date {date} --elite-only")

    if advanced:
        run_command(f"py scripts\\fetch_goalies.py --date {date}")
        run_command(f"py scripts\\fetch_advanced_metrics.py --date {date}")

    print("🎉 Pre-game pipeline complete!")
    print("\nUpload these files to your Claude Project:")
    print(f"   lineups_{date}.json")
    print(f"   verified_{date}.json")
    if advanced:
        print(f"   goalies_{date}.json")
        print(f"   advanced_metrics_{date}.json")
    print("\nThen paste the latest nightly prompt (Quick Fix v5). You're ready! 🔥")


def run_post_game(date):
    """Fetch last night's goal chains, then auto-score cold sticks + hot duo chains."""
    print(f"🏁 Post-game pipeline for {date}\n")

    # Step 1: pull chains from NHL API play-by-play
    run_command(f"py scripts\\fetch_postgame.py chains --date {date}")

    # Step 2: score predictions vs actual chains, print summary
    run_command(f"py scripts\\score_results.py --date {date}")

    print("📊 Post-game scoring complete.")
    print(f"   Results appended to data/results_log.csv")
    print(f"   Run 'py scripts\\score_results.py --summary' for cumulative stats.\n")


def main():
    parser = argparse.ArgumentParser(description="Nightly NHL Linemate pipeline")
    parser.add_argument("--advanced",  action="store_true",
                        help="Pre-game: also fetch goalies + advanced metrics")
    parser.add_argument("--post-game", action="store_true",
                        help="Post-game mode: fetch chains then auto-score results")
    parser.add_argument("--date",      default=None,
                        help="Override date (YYYY-MM-DD). Post-game defaults to yesterday.")
    args = parser.parse_args()

    if args.post_game:
        date = args.date or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        run_post_game(date)
    else:
        _, date = get_playing_teams()
        if args.date:
            date = args.date
        print(f"📅 Processing for {date}\n")
        run_pre_game(date, args.advanced)


if __name__ == "__main__":
    main()
