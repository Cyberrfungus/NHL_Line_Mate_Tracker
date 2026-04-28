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
from datetime import date as _date
from scripts.write_picks_file import write_picks


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
        run_command(
            f"py scripts\\fetch_advanced_metrics.py --date {date} "
            f"--goalies-json data\\goalies_{date}.json"
        )

    run_command(f"py scripts\\fetch_odds.py --date {date} --window pre")

    print(f"✅ Pipeline complete for {date}")
    print(f"✅ Fresh Hockey-Reference data used")
    print(f"✅ verified_{date}.json ready")
    print(f"✅ Pre-game prices fetched for all Tier A picks (bet365, DraftKings, Fanatics, FanDuel)")
    print()
    print("Next step:")
    print("1. Upload the 3 files to main Claude Project")
    print("2. Paste the v6 prompt to generate tonight's sheet (prices will now be included)")


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

# ----------------------------------------------------------------------
# Picks file + odds fetch integration
# ----------------------------------------------------------------------
today_iso = _date.today().isoformat()

# 1. Write the picks file the odds script reads
try:
    write_picks(
        date=today_iso,
        tier_a=tier_a_picks,    # <-- replace with your actual Tier A variable name
        duos=duo_picks,         # <-- replace with your actual duo variable name
    )
except NameError as e:
    print(f"[picks] SKIPPED: variable not defined yet -> {e}")
    print("[picks] Edit tonight.py to point write_picks() at your real lists.")
else:
    # 2. Pre-bet odds fetch
    try:
        subprocess.run(
            ["python", "scripts/fetch_odds.py", "--date", today_iso, "--window", "pre"],
            check=True,
        )
        print(f"[odds] pre-window fetch complete for {today_iso}")
    except subprocess.CalledProcessError as e:
        print(f"[odds] pre-window fetch FAILED: {e}")

# Closing-line fetch (run manually ~5 min before puck drop):
# python scripts/fetch_odds.py --date {today} --window close
