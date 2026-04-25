#!/usr/bin/env python3
"""
NHL Linemate Duo Correlation Tracker — TONIGHT.PY
One-command nightly pipeline (April 2026 Playoffs)
"""

import subprocess
import sys
from datetime import datetime

def get_todays_date():
    """Return today's date in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")

def get_playing_teams():
    """Simple manual input for playoffs (2-4 games). Easy to upgrade later."""
    date = get_todays_date()
    print(f"\n🏒 NHL Linemate Duo Tracker — {date}\n")
    print("Enter tonight's playing teams (comma-separated, e.g. EDM,ANA,VGK,UTA)")
    print("or just press Enter to use last known slate.")

    teams_input = input("> ").strip()

    if teams_input:
        teams = [t.strip().upper() for t in teams_input.split(",")]
    else:
        # Default fallback for quick testing
        teams = ["EDM", "ANA", "VGK", "UTA"]  # update as needed

    return teams, date

def run_command(cmd):
    """Run a command and show output"""
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
    teams, date = get_playing_teams()

    print(f"📅 Processing {len(teams)} teams for {date}\n")

    # 1. Fetch lineups
    run_command(f"py fetch_dfo.py --date {date} --teams {','.join(teams)}")

    # 2. Verify players (cold flags, L5 goals, etc.)
    run_command(f"py verify_players.py --date {date} --elite-only")

    print("🎉 Pipeline complete!")
    print("\nNext steps:")
    print("1. Upload these files to your Claude Project:")
    print(f"   - lineups_{date}.json")
    print(f"   - verified_{date}.json")
    print("2. Paste the latest nightly prompt (Quick Fix v5)")
    print("3. Review the Verified Play Sheet")
    print("\nYou're all set for tonight! 🔥")

if __name__ == "__main__":
    main()
