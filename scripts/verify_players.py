#!/usr/bin/env python3
"""
verify_players.py — Pull last 5 game logs for players in tonight's lineup.
Auto-detects cold streaks, hot streaks, and flags injured/scratched players.

Usage:
    py verify_players.py                     # Uses today's lineups file
    py verify_players.py --date 2026-04-14   # Specific date
    py verify_players.py --team ANA          # Single team only

Output: data/verified_YYYY-MM-DD.json + console report

Requires: requests (py -m pip install requests)
"""

import argparse
import json
import os
import sys
import time
from datetime import date, datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# NHL API base
NHL_API = "https://api-web.nhle.com"
SEARCH_API = "https://search.d3.nhle.com/api/v1/search/player"


def cold_sticks_tier(player_data):
    """
    Classify a player for the Cold Sticks under-targeting system.

    Target: player under 0.5 points.

    Returns:
        'A' — Locked cold, highest conviction (5+ blanks, 0 pts L5)
        'B' — Structural cold (3-4 blanks, low production)
        None — No play (variance, active, or insufficient signal)
    """
    blanks = player_data.get('consecutive_blanks', 0)
    l5_pts = player_data.get('last5_pts', 0)

    # Exclude star variance: few blanks but still producing
    # Protects against flagging MacKinnon-type players who had 2 off nights
    if blanks <= 2 and l5_pts >= 4:
        return None

    # Tier A: 5+ blanks with zero production
    if blanks >= 5 and l5_pts == 0:
        return 'A'

    # Tier B: 3-4 blanks with low production
    if blanks >= 3 and l5_pts <= 2:
        return 'B'

    return None


def find_player_id(name, session):
    """Search NHL API for player ID by name."""
    import requests
    try:
        resp = session.get(SEARCH_API, params={
            "culture": "en-us",
            "limit": 3,
            "q": name,
            "active": "true"
        }, timeout=10)
        results = resp.json()
        if results and len(results) > 0:
            # Return first match
            return results[0].get("playerId")
    except Exception as e:
        pass
    return None


def get_player_game_log(player_id, season="20252026", session=None):
    """Get player's game log for the season."""
    import requests
    if session is None:
        session = requests.Session()
    try:
        url = f"{NHL_API}/v1/player/{player_id}/game-log/{season}/2"
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def analyze_player(name, session, season="20252026"):
    """
    Find player, get last 5 games, return analysis dict.
    """
    pid = find_player_id(name, session)
    if not pid:
        return {"name": name, "status": "NOT_FOUND", "player_id": None}

    log_data = get_player_game_log(pid, season, session)
    if not log_data or "gameLog" not in log_data:
        return {"name": name, "status": "NO_GAMELOG", "player_id": pid}

    games = log_data["gameLog"]
    if not games:
        return {"name": name, "status": "NO_GAMES", "player_id": pid}

    # Last 5 games (most recent first)
    last5 = games[:5]

    # Extract stats
    game_entries = []
    consecutive_blanks = 0
    blank_streak_broken = False

    for g in last5:
        pts = g.get("points", 0)
        goals = g.get("goals", 0)
        assists = g.get("assists", 0)
        date_str = g.get("gameDate", "")
        opp = g.get("opponentAbbrev", "")
        toi = g.get("toi", "")

        game_entries.append({
            "date": date_str,
            "opp": opp,
            "g": goals,
            "a": assists,
            "pts": pts,
            "toi": toi
        })

        # Count consecutive blanks from most recent
        if not blank_streak_broken:
            if pts == 0:
                consecutive_blanks += 1
            else:
                blank_streak_broken = True

    # Total points in last 5
    total_pts = sum(g["pts"] for g in game_entries)
    total_goals = sum(g["g"] for g in game_entries)

    # Determine flags
    flags = []
    if consecutive_blanks >= 3:
        flags.append("COLD_3+")
    elif consecutive_blanks >= 2:
        flags.append("COLD_2")

    if total_pts >= 5:
        flags.append("HOT_5+")
    elif total_pts >= 3 and consecutive_blanks == 0:
        flags.append("HOT")

    # Check last game date to see if player is active
    last_game_date = last5[0].get("gameDate", "") if last5 else ""

    return {
        "name": name,
        "player_id": pid,
        "status": "ACTIVE",
        "last_game": last_game_date,
        "last5_pts": total_pts,
        "last5_goals": total_goals,
        "consecutive_blanks": consecutive_blanks,
        "flags": flags,
        "games": game_entries
    }


def main():
    try:
        import requests
    except ImportError:
        print("ERROR: Missing 'requests'. Install with:")
        print("  py -m pip install requests")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Verify player status and recent form")
    parser.add_argument("--date", default=None, help="Date for lineups file (YYYY-MM-DD)")
    parser.add_argument("--team", default=None, help="Single team to verify")
    parser.add_argument("--elite-only", action="store_true", help="Only check players on L1/L2/PP1/PP2")
    args = parser.parse_args()

    target_date = args.date or date.today().strftime("%Y-%m-%d")
    lineup_path = os.path.join(DATA_DIR, f"lineups_{target_date}.json")

    if not os.path.exists(lineup_path):
        print(f"ERROR: {lineup_path} not found")
        sys.exit(1)

    with open(lineup_path, "r", encoding="utf-8") as f:
        lineups = json.load(f)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    # Collect players to verify
    players_to_check = {}  # name -> team
    teams_to_check = [args.team.upper()] if args.team else list(lineups.keys())

    for team in teams_to_check:
        td = lineups.get(team, {})
        if "error" in td or "L1" not in td:
            continue

        if args.elite_only:
            keys = ["L1", "L2", "PP1", "PP2"]
        else:
            keys = ["L1", "L2", "L3", "L4", "PP1", "PP2"]

        for key in keys:
            for name in td.get(key, []):
                if name not in players_to_check:
                    players_to_check[name] = team

    print(f"Verifying {len(players_to_check)} players from {len(teams_to_check)} teams...")
    print()

    results = {}
    cold_players = []
    hot_players = []
    cold_sticks = []
    not_found = []

    for i, (name, team) in enumerate(players_to_check.items(), 1):
        print(f"  [{i}/{len(players_to_check)}] {name} ({team})...", end=" ", flush=True)

        analysis = analyze_player(name, session)

        if analysis["status"] == "NOT_FOUND":
            print("NOT FOUND")
            not_found.append(name)
        elif analysis["status"] in ("NO_GAMELOG", "NO_GAMES"):
            print(f"{analysis['status']}")
        else:
            pts = analysis["last5_pts"]
            blanks = analysis["consecutive_blanks"]
            flags_str = ", ".join(analysis["flags"]) if analysis["flags"] else "OK"
            last_game = analysis.get("last_game", "?")

            # Show last 5 as compact string
            games_str = " | ".join([
                f"{g['date'][-5:]} vs {g['opp']}: {g['pts']}pts"
                for g in analysis.get("games", [])[:5]
            ])

            if "COLD" in flags_str:
                print(f"⛔ {flags_str} ({blanks} blanks) | L5: {pts}pts | {games_str}")
                cold_players.append((name, team, blanks, pts))
            elif "HOT" in flags_str:
                print(f"🔥 {flags_str} | L5: {pts}pts | {games_str}")
                hot_players.append((name, team, pts, analysis.get("last5_goals", 0)))
            else:
                print(f"   {flags_str} | L5: {pts}pts | {games_str}")

            # Cold Sticks classification (independent of cold/hot flagging above)
            tier = cold_sticks_tier(analysis)
            if tier:
                cold_sticks.append({
                    "name": name,
                    "team": team,
                    "tier": tier,
                    "blanks": analysis["consecutive_blanks"],
                    "l5_pts": analysis["last5_pts"],
                    "l5_goals": analysis["last5_goals"]
                })

        results[name] = analysis

        # Rate limit: ~100ms between calls
        if i < len(players_to_check):
            time.sleep(0.15)

    # Sort cold sticks: Tier A first, then by most blanks descending
    cold_sticks.sort(key=lambda x: (x["tier"], -x["blanks"]))

    # Summary
    print()
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    if cold_players:
        print()
        print("⛔ COLD FLAGS (2+ consecutive blanks):")
        for name, team, blanks, pts in sorted(cold_players, key=lambda x: -x[2]):
            print(f"   {name} ({team}) — {blanks} consecutive blanks, {pts}pts in L5")

    if hot_players:
        print()
        print("🔥 HOT PLAYERS (3+ pts in L5, no blanks):")
        for name, team, pts, goals in sorted(hot_players, key=lambda x: -x[2]):
            print(f"   {name} ({team}) — {pts}pts ({goals}G) in L5")

    if cold_sticks:
        print()
        print("❄️  COLD STICKS (under 0.5 pts targets):")
        tier_a = [c for c in cold_sticks if c["tier"] == "A"]
        tier_b = [c for c in cold_sticks if c["tier"] == "B"]
        if tier_a:
            print(f"   TIER A ({len(tier_a)} plays — locked cold):")
            for c in tier_a:
                print(f"      {c['name']} ({c['team']}) — {c['blanks']} blanks, {c['l5_pts']}pts L5")
        if tier_b:
            print(f"   TIER B ({len(tier_b)} plays — structural cold):")
            for c in tier_b:
                print(f"      {c['name']} ({c['team']}) — {c['blanks']} blanks, {c['l5_pts']}pts L5")

    if not_found:
        print()
        print(f"⚠️  NOT FOUND ({len(not_found)}): {', '.join(not_found)}")

    # Save results
    out_path = os.path.join(DATA_DIR, f"verified_{target_date}.json")
    output = {
        "date": target_date,
        "verified_count": len(results),
        "cold_flags": [{"name": n, "team": t, "blanks": b, "l5_pts": p} for n, t, b, p in cold_players],
        "hot_players": [{"name": n, "team": t, "l5_pts": p, "l5_goals": g} for n, t, p, g in hot_players],
        "cold_sticks": cold_sticks,
        "not_found": not_found,
        "players": results
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print(f"Saved: {out_path}")
    tier_a_count = sum(1 for c in cold_sticks if c["tier"] == "A")
    tier_b_count = sum(1 for c in cold_sticks if c["tier"] == "B")
    print(f"Total: {len(results)} players | {len(cold_players)} cold | {len(hot_players)} hot | "
          f"{tier_a_count} sticks-A | {tier_b_count} sticks-B | {len(not_found)} not found")


if __name__ == "__main__":
    main()
