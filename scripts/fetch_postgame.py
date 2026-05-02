#!/usr/bin/env python3
"""
nhl_tracker.py — Combined NHL Line-Mate Tracker data fetcher

Commands:
  py nhl_tracker.py lineups          Fetch today's DFO lineups (all 32 teams via Selenium)
  py nhl_tracker.py chains           Fetch yesterday's goal chains (NHL API)
  py nhl_tracker.py chains --date 2026-04-09   Fetch chains for a specific date

Output:
  data/lineups_YYYY-MM-DD.json
  data/chains_YYYY-MM-DD.json
  data/chains_YYYY-MM-DD.csv

Setup (one time):
  py -m pip install selenium webdriver-manager beautifulsoup4 requests
"""
import requests, json, os, sys, re, time
from datetime import datetime, timedelta


# ══════════════════════════════════════════════════════
# SHARED CONFIG
# ══════════════════════════════════════════════════════

TEAM_SLUGS = {
    "ANA":"anaheim-ducks",     "BOS":"boston-bruins",
    "BUF":"buffalo-sabres",    "CGY":"calgary-flames",
    "CAR":"carolina-hurricanes","CHI":"chicago-blackhawks",
    "COL":"colorado-avalanche", "CBJ":"columbus-blue-jackets",
    "DAL":"dallas-stars",      "DET":"detroit-red-wings",
    "EDM":"edmonton-oilers",   "FLA":"florida-panthers",
    "LAK":"los-angeles-kings", "MIN":"minnesota-wild",
    "MTL":"montreal-canadiens","NSH":"nashville-predators",
    "NJD":"new-jersey-devils", "NYI":"new-york-islanders",
    "NYR":"new-york-rangers",  "OTT":"ottawa-senators",
    "PHI":"philadelphia-flyers","PIT":"pittsburgh-penguins",
    "SJS":"san-jose-sharks",   "SEA":"seattle-kraken",
    "STL":"st-louis-blues",    "TBL":"tampa-bay-lightning",
    "TOR":"toronto-maple-leafs","UTA":"utah-mammoth",
    "VAN":"vancouver-canucks", "VGK":"vegas-golden-knights",
    "WPG":"winnipeg-jets",
}


# ══════════════════════════════════════════════════════
# LINEUPS — DFO via Selenium
# ══════════════════════════════════════════════════════

def setup_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 Chrome/125.0 Safari/537.36")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=opts)
    except Exception:
        return webdriver.Chrome(options=opts)


def fetch_dfo_selenium(driver, team_slug):
    from bs4 import BeautifulSoup

    url = f"https://www.dailyfaceoff.com/teams/{team_slug}/line-combinations"
    driver.get(url)
    time.sleep(3)
    html = driver.page_source

    dfo_updated = ""
    m = re.search(r'Last updated:\s*([\d\-T:.]+Z?)', html)
    if m:
        dfo_updated = m.group(1)

    soup = BeautifulSoup(html, "html.parser")
    player_links = soup.find_all("a", href=re.compile(r"/players/news/"))
    names = []
    for link in player_links:
        text = link.get_text(strip=True)
        if text and len(text) > 2:
            names.append(text)

    cleaned = []
    for n in names:
        if not cleaned or n != cleaned[-1]:
            cleaned.append(n)

    fwd = cleaned[:12]
    d   = cleaned[12:18]
    pp  = cleaned[18:28]

    def chunk(lst, size):
        return [lst[i:i+size] for i in range(0, len(lst), size)]

    fwd_lines = chunk(fwd, 3)
    d_pairs   = chunk(d, 2)

    return {
        "updated": datetime.now().isoformat(),
        "dfo_updated": dfo_updated,
        "source": "DFO-selenium",
        "L1": fwd_lines[0] if len(fwd_lines) > 0 else [],
        "L2": fwd_lines[1] if len(fwd_lines) > 1 else [],
        "L3": fwd_lines[2] if len(fwd_lines) > 2 else [],
        "L4": fwd_lines[3] if len(fwd_lines) > 3 else [],
        "D1": d_pairs[0] if len(d_pairs) > 0 else [],
        "D2": d_pairs[1] if len(d_pairs) > 1 else [],
        "D3": d_pairs[2] if len(d_pairs) > 2 else [],
        "PP1": pp[:5] if len(pp) >= 5 else pp,
        "PP2": pp[5:10] if len(pp) >= 10 else pp[5:] if len(pp) > 5 else [],
        "injuries": [],
        "stats": {},
        "_raw_count": len(cleaned),
    }


def run_lineups():
    print("=" * 55)
    print("  NHL Tracker — Fetch Lineups (DFO Selenium)")
    print("=" * 55)

    print("\nInitializing headless Chrome...")
    driver = setup_driver()
    print("✅ Chrome ready\n")

    lineups = {}
    for abbrev, slug in TEAM_SLUGS.items():
        print(f"  → {abbrev}", end="  ", flush=True)
        try:
            result = fetch_dfo_selenium(driver, slug)
            count = result.get("_raw_count", 0)
            if count >= 18:
                print(f"✅ {count} players")
            elif count > 0:
                print(f"⚠️  {count} players (partial)")
            else:
                print(f"❌ 0 players")
        except Exception as e:
            result = {"updated": datetime.now().isoformat(), "error": str(e)}
            print(f"❌ {str(e)[:60]}")

        lineups[abbrev] = result
        time.sleep(0.5)

    driver.quit()

    os.makedirs("data", exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"data/lineups_{date_str}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(lineups, f, indent=2, ensure_ascii=False)

    ok = sum(1 for v in lineups.values() if v.get("_raw_count", 0) >= 18)
    print(f"\n{'=' * 55}")
    print(f"  ✅ Created {filename}")
    print(f"     {ok}/{len(lineups)} teams with full data")
    print(f"{'=' * 55}")


# ══════════════════════════════════════════════════════
# CHAINS — NHL API (post-game)
# ══════════════════════════════════════════════════════

def get_schedule(date_str):
    url = f"https://api-web.nhle.com/v1/schedule/{date_str}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    games = []
    for week in data.get("gameWeek", []):
        if week.get("date") != date_str:
            continue
        for g in week.get("games", []):
            games.append({
                "id": g["id"],
                "away": g["awayTeam"]["abbrev"],
                "home": g["homeTeam"]["abbrev"],
                "state": g.get("gameState", "?"),
                "away_score": g["awayTeam"].get("score", 0),
                "home_score": g["homeTeam"].get("score", 0),
            })
    return games


def get_strength(situation_code, scoring_team_id, away_team_id, period_type):
    if not situation_code or len(str(situation_code)) != 4:
        return "ES"
    sc = str(situation_code)
    away_goalie  = int(sc[0])
    away_skaters = int(sc[1])
    home_skaters = int(sc[2])
    home_goalie  = int(sc[3])

    # Bug 11 fix: shootout goals must be tagged SO, not ES
    if period_type == "SO":
        return "SO"

    if period_type == "OT":
        return "OT"

    is_home = scoring_team_id != away_team_id
    if is_home and away_goalie == 0:
        return "EN"
    if not is_home and home_goalie == 0:
        return "EN"

    if away_skaters != home_skaters:
        if is_home:
            return "PP" if home_skaters > away_skaters else "SH"
        else:
            return "PP" if away_skaters > home_skaters else "SH"

    return "ES"


def build_player_map(pbp_data):
    pmap = {}
    for player in pbp_data.get("rosterSpots", []):
        pid = player["playerId"]
        first = player.get("firstName", {}).get("default", "")
        last = player.get("lastName", {}).get("default", "")
        pmap[pid] = {
            "name": f"{first} {last}",
            "teamId": player.get("teamId"),
        }
    return pmap


def extract_goals(pbp_data, game_info, date_str):
    pmap = build_player_map(pbp_data)
    away_team_id = pbp_data.get("awayTeam", {}).get("id")
    goals = []

    for play in pbp_data.get("plays", []):
        if play.get("typeDescKey") != "goal":
            continue

        period = play.get("periodDescriptor", {})
        period_num = period.get("number", 0)
        period_type = period.get("periodType", "REG")
        time_in = play.get("timeInPeriod", "00:00")
        situation = play.get("situationCode", "1551")
        details = play.get("details", {})
        scoring_team_id = details.get("eventOwnerTeamId")

        team = game_info["away"] if scoring_team_id == away_team_id else game_info["home"]
        strength = get_strength(situation, scoring_team_id, away_team_id, period_type)

        scorer_id = details.get("scoringPlayerId")
        scorer = pmap.get(scorer_id, {}).get("name", "Unknown")
        a1_id = details.get("assist1PlayerId")
        a2_id = details.get("assist2PlayerId")
        assist1 = pmap.get(a1_id, {}).get("name") if a1_id else None
        assist2 = pmap.get(a2_id, {}).get("name") if a2_id else None

        # Bug 12: blocklist — strings that must never appear as players in chain
        CHAIN_BLOCKLIST = {"unassisted", "unknown", ""}

        # Bug 10 fix: filter blocklist strings from chain; "unassisted" is only
        # a display label for assist1 JSON field, not a real player name.
        def _valid(name):
            return bool(name) and name.lower() not in CHAIN_BLOCKLIST

        goals.append({
            "date": date_str,
            "game": f"{game_info['away']}@{game_info['home']}",
            "team": team,
            "period": period_num,
            "time": time_in,
            "strength": strength,
            "scorer": scorer,
            "assist1": assist1 if assist1 and _valid(assist1) else "unassisted",
            "assist2": assist2 if assist2 and _valid(assist2) else "",
            "chain": [scorer] + ([assist1] if _valid(assist1) else []) + ([assist2] if _valid(assist2) else []),
        })

    return goals


def fetch_game_pbp(game_id):
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def run_chains(date_str):
    print("=" * 55)
    print(f"  NHL Tracker — Fetch Chains ({date_str} slate)")
    print("=" * 55)

    print(f"\nFetching schedule...")
    games = get_schedule(date_str)

    if not games:
        print(f"No games found for {date_str}")
        return

    print(f"Found {len(games)} games:\n")
    for g in games:
        icon = "✅" if g["state"] in ("OFF", "FINAL") else "🔴" if g["state"] == "LIVE" else "⏳"
        print(f"  {icon} {g['away']} {g['away_score']} @ {g['home']} {g['home_score']}  ({g['state']})")

    all_goals = []
    for g in games:
        if g["state"] not in ("OFF", "FINAL"):
            print(f"\n  ⚠️  {g['away']}@{g['home']} not final, skipping")
            continue

        print(f"\n  Fetching: {g['away']}@{g['home']}...", end=" ", flush=True)
        try:
            pbp = fetch_game_pbp(g["id"])
            goals = extract_goals(pbp, g, date_str)
            all_goals.extend(goals)
            print(f"✅ {len(goals)} goals")
        except Exception as e:
            print(f"❌ {e}")
        time.sleep(0.3)

    os.makedirs("data", exist_ok=True)

    # JSON
    output = {
        "date": date_str,
        "games_count": len(games),
        "goals_count": len(all_goals),
        "games": [
            {"label": f"{g['away']}@{g['home']}", "score": f"{g['away_score']}-{g['home_score']}", "state": g["state"]}
            for g in games
        ],
        "goals": all_goals,
    }
    json_file = f"data/chains_{date_str}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # CSV
    csv_file = f"data/chains_{date_str}.csv"
    with open(csv_file, "w", encoding="utf-8") as f:
        f.write("date,game,team,period,time,strength,scorer,assist1,assist2\n")
        for g in all_goals:
            row = [g["date"], g["game"], g["team"], str(g["period"]), g["time"],
                   g["strength"], g["scorer"], g["assist1"], g["assist2"]]
            f.write(",".join(f'"{v}"' for v in row) + "\n")

    print(f"\n{'=' * 55}")
    print(f"  ✅ {len(all_goals)} goals from {len(games)} games")
    print(f"  📄 {json_file}")
    print(f"  📄 {csv_file}")
    print(f"{'=' * 55}")

    print(f"\n  CHAIN SUMMARY:")
    for g in all_goals:
        chain_str = " → ".join(g["chain"])
        print(f"    [{g['strength']:2s}] {g['team']:3s} P{g['period']} {g['time']}  {chain_str}")


# ══════════════════════════════════════════════════════
# MAIN — command router
# ══════════════════════════════════════════════════════

def print_usage():
    print("""
NHL Line-Mate Tracker — Data Fetcher
=====================================

Usage:
  py nhl_tracker.py lineups              Fetch today's lineups from DFO (Selenium)
  py nhl_tracker.py chains               Fetch yesterday's goal chains (NHL API)
  py nhl_tracker.py chains --date YYYY-MM-DD   Fetch chains for specific date

Examples:
  py nhl_tracker.py lineups
  py nhl_tracker.py chains
  py nhl_tracker.py chains --date 2026-04-09
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "lineups":
        run_lineups()

    elif command == "chains":
        date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if "--date" in sys.argv:
            idx = sys.argv.index("--date")
            if idx + 1 < len(sys.argv):
                date_str = sys.argv[idx + 1]
        run_chains(date_str)

    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()