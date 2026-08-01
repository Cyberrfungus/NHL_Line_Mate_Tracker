#!/usr/bin/env python3
"""
NHL Linemate Duo Correlation Tracker — TONIGHT.PY
One-command nightly pipeline

Usage:
    py tonight.py                   # pre-game: lineups + verify
    py tonight.py --advanced        # pre-game: lineups + verify + goalies + advanced metrics
    py tonight.py --post-game       # post-game: fetch chains + auto-score vs predictions
    py tonight.py --post-game --date 2026-04-21   # score a specific past date

Note: run_pregame.bat / run_postgame.bat wrap the same sequences for
double-click use on Windows.
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"


def run_command(script, *args, fatal=True):
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    print(f"🚀 Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=ROOT)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print("STDERR:", result.stderr.strip())
        print("✅ Done\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stdout:
            print(e.stdout.strip())
        if e.stderr:
            print("STDERR:", e.stderr.strip())
        if fatal:
            sys.exit(1)
        return False


def run_pre_game(date, advanced):
    """Fetch lineups, verify players, and optionally pull advanced signals."""
    run_command("fetch_lineups_nhl.py", "--date", date)
    run_command("verify_players.py", "--date", date, "--elite-only")

    if advanced:
        goalies_ok = run_command("fetch_goalies.py", "--date", date, fatal=False)
        metrics_args = ["--date", date]
        if goalies_ok:
            metrics_args += ["--goalies-json", str(ROOT / "data" / f"goalies_{date}.json")]
        run_command("fetch_advanced_metrics.py", *metrics_args)

    # Odds fetch is optional — requires ODDS_API_KEY env var; never blocks the pipeline
    run_command("fetch_odds.py", "--date", date, "--window", "pre", fatal=False)

    print(f"✅ Pipeline complete for {date}")
    print(f"✅ verified_{date}.json ready")
    print()
    print("Next step:")
    print("1. Upload verified / lineups / advanced_metrics JSONs to main Claude Project")
    print("2. Paste the v6 prompt to generate tonight's sheet")


def run_post_game(date):
    """Fetch last night's goal chains, then auto-score cold sticks + hot duo chains."""
    print(f"🏁 Post-game pipeline for {date}\n")

    run_command("fetch_postgame.py", "chains", "--date", date)
    run_command("score_results.py", "--date", date)

    print("📊 Post-game scoring complete.")
    print("   Results appended to data/results_log.csv")
    print("   Run 'py scripts\\score_results.py --summary' for cumulative stats.\n")


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
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Processing for {date}\n")
        run_pre_game(date, args.advanced)


if __name__ == "__main__":
    main()
