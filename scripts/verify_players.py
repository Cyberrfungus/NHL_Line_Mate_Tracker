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

try:
    from scripts.utils import derive_season_code, detect_regime
except ImportError:
    from utils import derive_season_code, detect_regime

# Data quality filters — applied before any tier assignment
MIN_TOI_MINUTES = 8.0       # ignore games where player had < 8 min (scratches / IR returns)
MIN_QUALIFYING_GAMES = 3    # need at least 3 qualifying games to assign any hot/cold tier

# Staleness window per regime: regular-season teams play every 2-3 days;
# playoff series gaps + inter-round breaks can stretch 7-10 days.
STALENESS_DAYS = {"regular": 7, "playoffs": 14}
MAX_STALENESS_DAYS = STALENESS_DAYS["playoffs"]  # overwritten in main() by regime

# Hockey-Reference playoff skater stats (cumulative, updated daily).
# Playoffs ONLY — the cumulative table works for short playoff samples but
# cannot produce last-5 / blank-streak data from a 40+ GP regular season.
HOCKEYREF_SKATERS_URL = "https://www.hockey-reference.com/playoffs/NHL_{year}_skaters.html"


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


def parse_toi_minutes(toi_str: str) -> float:
    """Parse 'MM:SS' string → total minutes as float. Returns 0.0 on bad input."""
    try:
        parts = str(toi_str).split(":")
        return int(parts[0]) + int(parts[1]) / 60
    except (AttributeError, ValueError, IndexError):
        return 0.0


def _normalize_name(name: str) -> str:
    """Lowercase, strip accents, collapse spaces — for fuzzy player-name matching."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_name.lower().split())


def _hr_lookup(name: str, hr_map: dict) -> dict | None:
    """Find player in HR map: exact match first, then accent/case-normalised match."""
    if name in hr_map:
        return hr_map[name]
    norm = _normalize_name(name)
    for k, v in hr_map.items():
        if _normalize_name(k) == norm:
            return v
    return None


def fetch_hr_playoff_map(url: str) -> dict:
    """
    Scrape Hockey-Reference cumulative playoff skater stats.
    Returns {player_name: {team, gp, pts, g, a, atoi_min}} or {} on failure.
    HR hides stats tables in HTML comments — checks both visible DOM and comments.
    """
    import requests
    try:
        from bs4 import BeautifulSoup, Comment
    except ImportError:
        print("    [HR] beautifulsoup4 not installed — skipping HR source")
        return {}

    _HR_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.hockey-reference.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    try:
        # Prime the session with the HR homepage so we arrive with real cookies,
        # then request the stats page — mirrors how a browser navigates the site.
        _sess = requests.Session()
        try:
            _sess.get("https://www.hockey-reference.com/", timeout=10, headers=_HR_HEADERS)
        except Exception:
            pass  # homepage prime is best-effort; continue regardless
        resp = _sess.get(url, timeout=20, headers=_HR_HEADERS)
        resp.raise_for_status()
    except Exception as e:
        print(f"    [HR] fetch failed: {e}")
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")

    def _find_table(search_soup):
        for tid in ("stats", "skaters", "skaterstats"):
            t = search_soup.find("table", id=tid)
            if t:
                hs = [th.get_text(strip=True) for th in t.find_all("th")]
                if "PTS" in hs and "GP" in hs:
                    return t
        for t in search_soup.find_all("table"):
            hs = [th.get_text(strip=True) for th in t.find_all("th")]
            if "PTS" in hs and "GP" in hs and any(h in ("Tm", "Team") for h in hs):
                return t
        return None

    table = _find_table(soup)
    if table is None:
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            if "PTS" not in str(comment):
                continue
            table = _find_table(BeautifulSoup(str(comment), "html.parser"))
            if table is not None:
                break

    if table is None:
        print("    [HR] skater table not found in page or comments")
        return {}

    thead = table.find("thead")
    header_row = thead.find_all("tr")[-1] if thead else None
    if header_row is None:
        return {}
    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

    def _col(*names):
        for n in names:
            try:
                return headers.index(n)
            except ValueError:
                pass
        return None

    name_idx = _col("Player")
    tm_idx   = _col("Tm", "Team")
    gp_idx   = _col("GP")
    g_idx    = _col("G")
    a_idx    = _col("A")
    pts_idx  = _col("PTS")
    atoi_idx = _col("ATOI", "TOI")

    if any(i is None for i in [name_idx, tm_idx, gp_idx, pts_idx]):
        print(f"    [HR] missing required columns — name:{name_idx} tm:{tm_idx} gp:{gp_idx} pts:{pts_idx}")
        return {}

    result = {}
    tbody = table.find("tbody") or table
    for row in tbody.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if not cells or cells[0].name == "th":
            continue
        req = max(c for c in [name_idx, tm_idx, gp_idx, pts_idx] if c is not None)
        if len(cells) <= req:
            continue

        player_name = cells[name_idx].get_text(strip=True)
        if not player_name or player_name in ("", "Player"):
            continue

        team_raw = cells[tm_idx].get_text(strip=True)
        if team_raw in ("", "TOT", "nan"):
            continue

        def _int(idx):
            if idx is None or idx >= len(cells):
                return 0
            try:
                return int(float(cells[idx].get_text(strip=True) or 0))
            except (ValueError, TypeError):
                return 0

        gp = _int(gp_idx)
        if gp == 0:
            continue

        atoi_min = 0.0
        if atoi_idx is not None and atoi_idx < len(cells):
            atoi_min = parse_toi_minutes(cells[atoi_idx].get_text(strip=True))

        result[player_name] = {
            "team":     team_raw,
            "gp":       gp,
            "pts":      _int(pts_idx),
            "g":        _int(g_idx),
            "a":        _int(a_idx),
            "atoi_min": atoi_min,
        }

    return result


def _build_from_hr(name: str, hr_data: dict, slate_date: str) -> dict:
    """
    Synthesise an analysis dict from Hockey-Reference cumulative playoff stats.
    consecutive_blanks is only definitive when total pts == 0; otherwise 0 (conservative).
    """
    gp      = hr_data["gp"]
    pts     = hr_data["pts"]
    g       = hr_data["g"]
    atoi_min = hr_data.get("atoi_min", 0.0)

    # TOI floor check: ATOI must meet minimum
    if atoi_min > 0 and atoi_min < MIN_TOI_MINUTES:
        return {
            "name": name, "player_id": None,
            "status": "INSUFFICIENT_QUALIFYING_GAMES",
            "qualifying_games": 0, "last_game": "",
        }

    if gp < MIN_QUALIFYING_GAMES:
        return {
            "name": name, "player_id": None,
            "status": "INSUFFICIENT_QUALIFYING_GAMES",
            "qualifying_games": gp, "last_game": "",
        }

    # L5 metrics: exact when GP ≤ 5, rate-scaled otherwise
    l5_pts   = pts if gp <= 5 else round(pts / gp * 5)
    l5_goals = g   if gp <= 5 else round(g   / gp * 5)

    # Consecutive blanks: only deterministic when all games were pointless
    consecutive_blanks = gp if pts == 0 else 0

    flags = []
    if consecutive_blanks >= 3:
        flags.append("COLD_3+")
    elif consecutive_blanks >= 2:
        flags.append("COLD_2")
    if l5_pts >= 5:
        flags.append("HOT_5+")
    elif l5_pts >= 3 and consecutive_blanks == 0:
        flags.append("HOT")

    mins = int(atoi_min)
    secs = int(round((atoi_min - mins) * 60))
    atoi_str = f"{mins}:{secs:02d}" if atoi_min > 0 else "?"

    return {
        "name":               name,
        "player_id":          None,
        "status":             "ACTIVE",
        "source":             "hockey-reference",
        "last_game":          slate_date or "",
        "last5_pts":          l5_pts,
        "last5_goals":        l5_goals,
        "consecutive_blanks": consecutive_blanks,
        "flags":              flags,
        "games":              [],
        "hr_gp":              gp,
        "hr_pts":             pts,
        "hr_atoi":            atoi_str,
    }


def find_player_id(name, session, team=None):
    """Search NHL API for player ID by name, with optional team validation."""
    import requests
    try:
        resp = session.get(SEARCH_API, params={
            "culture": "en-us",
            "limit": 10,
            "q": name,
            "active": "true"
        }, timeout=10)
        results = resp.json()
        if not results:
            return None
        if team:
            team_upper = team.upper()
            for r in results:
                r_team = (
                    r.get("currentTeamAbbrev")
                    or r.get("teamAbbrev")
                    or r.get("teamCode")
                    or ""
                ).upper()
                if r_team == team_upper:
                    return r.get("playerId")
        # Fall back to first result if team filter found nothing
        return results[0].get("playerId")
    except Exception:
        pass
    return None


def get_player_game_log(player_id, season="20252026", session=None, game_type=2):
    """Get player's game log. game_type: 2 = regular season, 3 = playoffs."""
    import requests
    if session is None:
        session = requests.Session()
    try:
        url = f"{NHL_API}/v1/player/{player_id}/game-log/{season}/{game_type}"
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def analyze_player(name, session, season="20252026", slate_date=None, hr_map=None,
                   team=None, game_type=3):
    """
    Find player, get last 5 qualifying games, return analysis dict.

    Source priority by regime:
      PLAYOFFS (game_type=3):
        1. Hockey-Reference cumulative playoff stats (hr_map) — fresh daily scrape
        2. NHL API playoff game log — per-game, accurate blanks count
      REGULAR SEASON (game_type=2, hr_map must be None):
        NHL API regular-season game log is the primary and only source — the
        per-game log gives true last-5 and blank streaks, which HR's cumulative
        table cannot provide over a 40+ GP season.
      Cross-regime leakage is the failure mode that caused the April 2026 stale
      data audit finding: never feed regular-season logs into a playoff slate.

    Qualifying game criteria (applied before any tier assignment):
      - TOI >= MIN_TOI_MINUTES (filters scratches and brief IR returns)
      - Most recent qualifying game within MAX_STALENESS_DAYS of slate_date
      - At least MIN_QUALIFYING_GAMES qualifying games in the sample
    """
    # Primary path (playoffs only): Hockey-Reference cumulative playoff data
    if hr_map is not None:
        hr_data = _hr_lookup(name, hr_map)
        if hr_data is not None:
            return _build_from_hr(name, hr_data, slate_date)

    pid = find_player_id(name, session, team=team)
    if not pid:
        return {"name": name, "status": "NOT_FOUND", "player_id": None}

    log_data = get_player_game_log(pid, season, session, game_type=game_type)

    if not log_data or "gameLog" not in log_data:
        return {"name": name, "status": "NO_GAMELOG", "player_id": pid}

    games = log_data["gameLog"]
    if not games:
        empty_status = "NO_PLAYOFF_GAMES" if game_type == 3 else "NO_GAMES"
        return {"name": name, "status": empty_status, "player_id": pid}

    # Filter 1 — TOI floor: each game must meet the minimum ice-time threshold
    qualified_games = [
        g for g in games
        if parse_toi_minutes(g.get("toi", "")) >= MIN_TOI_MINUTES
    ]

    # Filter 2 — Staleness: most recent qualifying game must be within MAX_STALENESS_DAYS
    if slate_date and qualified_games:
        try:
            slate_dt = datetime.strptime(slate_date, "%Y-%m-%d").date()
            last_q_dt = datetime.strptime(qualified_games[0]["gameDate"], "%Y-%m-%d").date()
            days_stale = (slate_dt - last_q_dt).days
            if days_stale > MAX_STALENESS_DAYS:
                return {
                    "name": name,
                    "player_id": pid,
                    "status": "STALE_DATA",
                    "last_game": qualified_games[0]["gameDate"],
                    "days_stale": days_stale,
                }
        except (ValueError, KeyError):
            pass

    # Filter 3 — Minimum sample: need at least MIN_QUALIFYING_GAMES to assign any tier
    if len(qualified_games) < MIN_QUALIFYING_GAMES:
        return {
            "name": name,
            "player_id": pid,
            "status": "INSUFFICIENT_QUALIFYING_GAMES",
            "qualifying_games": len(qualified_games),
            "last_game": qualified_games[0]["gameDate"] if qualified_games else "",
        }

    # Last 5 qualifying games (most recent first)
    last5 = qualified_games[:5]

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
    parser.add_argument("--regime", choices=["auto", "regular", "playoffs"], default="auto",
                        help="Data regime: regular season or playoffs (default: auto-detect from date)")
    args = parser.parse_args()

    target_date = args.date or date.today().strftime("%Y-%m-%d")

    # Resolve regime → data sources, game_type, and staleness window
    global MAX_STALENESS_DAYS
    regime = detect_regime(target_date) if args.regime == "auto" else args.regime
    game_type = 3 if regime == "playoffs" else 2
    MAX_STALENESS_DAYS = STALENESS_DAYS[regime]
    season = derive_season_code(target_date)
    print(f"📅 Regime: {regime.upper()}  |  season {season}  |  "
          f"staleness window {MAX_STALENESS_DAYS}d"
          + ("  (auto-detected — pass --regime to override)" if args.regime == "auto" else ""))

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

    player_roles = {}  # name -> list of roles (e.g. ["L2", "PP2"])

    # Build injury map: any player flagged out/ir/dtd or scratched is marked INACTIVE
    # and excluded from API lookups — they cannot generate meaningful game log data.
    INACTIVE_STATUSES = {"out", "ir", "dtd", "scratched"}
    injured_map = {}  # name -> status string
    for team in teams_to_check:
        td = lineups.get(team, {})
        for inj in td.get("injuries", []):
            p = inj.get("player", "")
            s = inj.get("status", "").lower()
            if p and s in INACTIVE_STATUSES:
                injured_map[p] = s
        for p in td.get("scratched", []):
            if p:
                injured_map[p] = "scratched"

    injured_in_slots = {}  # name -> {team, status} — injured players found in active slots

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
                if name in injured_map:
                    if name not in injured_in_slots:
                        injured_in_slots[name] = {"team": team, "status": injured_map[name]}
                    continue  # skip — will be written as INACTIVE
                if name not in players_to_check:
                    players_to_check[name] = team
                if name not in player_roles:
                    player_roles[name] = []
                if key not in player_roles[name]:
                    player_roles[name].append(key)

    # Playoffs: Hockey-Reference cumulative stats as primary data source.
    # Regular season: skip HR entirely — NHL API per-game log is primary.
    hr_map = None
    if regime == "playoffs":
        hr_year = target_date[:4]
        hr_url = HOCKEYREF_SKATERS_URL.format(year=hr_year)
        print(f"Fetching Hockey-Reference playoff skater stats ({hr_url})...")
        hr_map = fetch_hr_playoff_map(hr_url)
        if hr_map:
            print(f"✅ Using fresh Hockey-Reference playoff skater data ({len(hr_map)} players parsed)")
        else:
            print("⚠️  Hockey-Reference unavailable — falling back to NHL API playoff log")
    else:
        print("Using NHL API regular-season game logs (per-game last-5 + blank streaks)")
    print()

    if injured_in_slots:
        print(f"Skipping {len(injured_in_slots)} injured/out/dtd player(s) — will be marked INACTIVE:")
        for inj_name, inj_info in injured_in_slots.items():
            print(f"  {inj_name} ({inj_info['team']}) — {inj_info['status'].upper()}")
        print()

    print(f"Verifying {len(players_to_check)} players from {len(teams_to_check)} teams...")
    print()

    results = {}
    cold_players = []
    hot_players = []
    cold_sticks = []
    not_found = []

    for i, (name, team) in enumerate(players_to_check.items(), 1):
        print(f"  [{i}/{len(players_to_check)}] {name} ({team})...", end=" ", flush=True)

        analysis = analyze_player(name, session, season=season, slate_date=target_date,
                                  hr_map=hr_map, team=team, game_type=game_type)

        if analysis["status"] == "NOT_FOUND":
            print("NOT FOUND")
            not_found.append(name)
        elif analysis["status"] in ("NO_GAMELOG", "NO_GAMES", "NO_PLAYOFF_GAMES"):
            print(f"{analysis['status']}")
        elif analysis["status"] == "STALE_DATA":
            days = analysis.get("days_stale", "?")
            last = analysis.get("last_game", "?")
            print(f"⚠️  STALE ({days}d — last qualifying game {last}) — excluded from tiers")
        elif analysis["status"] == "INSUFFICIENT_QUALIFYING_GAMES":
            n = analysis.get("qualifying_games", 0)
            print(f"⚠️  SKIP ({n} qualifying games < {MIN_QUALIFYING_GAMES} required) — excluded from tiers")
        else:
            pts = analysis["last5_pts"]
            blanks = analysis["consecutive_blanks"]
            flags_str = ", ".join(analysis["flags"]) if analysis["flags"] else "OK"
            last_game = analysis.get("last_game", "?")

            # Show game data: per-game detail (NHL API) or cumulative summary (HR)
            source = analysis.get("source", "")
            if source == "hockey-reference":
                gp   = analysis.get("hr_gp", "?")
                atoi = analysis.get("hr_atoi", "?")
                games_str = f"[HR playoff] {gp}GP | ATOI {atoi}"
            else:
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
                roles = player_roles.get(name, [])
                es_roles = [r for r in roles if r.startswith("L")]
                pp_roles = [r for r in roles if r.startswith("PP")]
                line_role = "+".join(sorted(es_roles) + sorted(pp_roles))
                high_role = any(r in ("L1", "L2", "PP1") for r in roles)
                cold_sticks.append({
                    "name": name,
                    "team": team,
                    "tier": tier,
                    "blanks": analysis["consecutive_blanks"],
                    "l5_pts": analysis["last5_pts"],
                    "l5_goals": analysis["last5_goals"],
                    "line_role": line_role or "?",
                    "high_role": high_role
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
            print(f"   TIER A ({len(tier_a)} plays — 86% WR, u0.5 pts primary prop):")
            for c in tier_a:
                flag = " ⚠ HIGH-ROLE" if c.get("high_role") else ""
                print(f"      {c['name']} ({c['team']}) [{c.get('line_role','?')}] — {c['blanks']} blanks, {c['l5_pts']}pts L5{flag}")
        if tier_b:
            print(f"   TIER B ({len(tier_b)} plays — 70% WR, small size only):")
            for c in tier_b:
                flag = " ⚠ HIGH-ROLE" if c.get("high_role") else ""
                print(f"      {c['name']} ({c['team']}) [{c.get('line_role','?')}] — {c['blanks']} blanks, {c['l5_pts']}pts L5{flag}")

    if not_found:
        print()
        print(f"⚠️  NOT FOUND ({len(not_found)}): {', '.join(not_found)}")

    # Write INACTIVE entries for injured/out/dtd players found in lineup slots
    for inj_name, inj_info in injured_in_slots.items():
        results[inj_name] = {
            "name": inj_name,
            "status": "INACTIVE",
            "player_id": None,
            "injury_status": inj_info["status"],
        }

    # Save results
    out_path = os.path.join(DATA_DIR, f"verified_{target_date}.json")
    output = {
        "date": target_date,
        "regime": regime,
        "season": season,
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