#!/usr/bin/env python3
"""
fetch_advanced_metrics.py
Download team + goalie advanced stats from MoneyPuck.
Outputs data/advanced_metrics_YYYY-MM-DD.json

Usage:
    python scripts/fetch_advanced_metrics.py --date 2026-04-23
    python scripts/fetch_advanced_metrics.py --date 2026-04-23 --season 2025
    python scripts/fetch_advanced_metrics.py --date 2026-04-23 --print-only
    python scripts/fetch_advanced_metrics.py --date 2026-04-23 --debug-cols

MoneyPuck data: https://moneypuck.com/data.htm
"""

import argparse
import json
import os
import sys
import unicodedata
from datetime import datetime
from io import StringIO
from pathlib import Path

import requests
import pandas as pd

try:
    from scripts.utils import get_playoff_goalie_weight
except ImportError:
    from utils import get_playoff_goalie_weight

BASE_URL             = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{season}/regular"
PLAYOFF_BASE_URL     = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{season}/playoffs"
# Primary playoff source: Hockey-Reference updates daily, usually by ~5:40 AM after games.
# {year} is the playoff year (season start year + 1, e.g. 2025 season → 2026 playoffs).
HOCKEYREF_PLAYOFF_URL = "https://www.hockey-reference.com/playoffs/NHL_{year}_goalies.html"
# Applied when playoffs are underway but no data source has populated yet.
# Signals "playoff mode, low confidence" without misrepresenting the blend ratio.
PLAYOFF_FALLBACK_WEIGHT = 0.10
HEADERS = {"User-Agent": "NHL-Line-Mate-Tracker/1.0"}

# MoneyPuck abbrevs that differ from project standard
TEAM_NORM = {
    "T.B": "TBL", "N.J": "NJD", "S.J": "SJS", "L.A": "LAK",
    "T.B.": "TBL", "N.J.": "NJD", "S.J.": "SJS", "L.A.": "LAK",
}

# Hockey-Reference abbrevs that differ from project standard
HOCKEYREF_TEAM_NORM = {
    "L.A":  "LAK", "L.A.": "LAK",
    "T.B":  "TBL", "T.B.": "TBL",
    "N.J":  "NJD", "N.J.": "NJD",
    "S.J":  "SJS", "S.J.": "SJS",
    "VEG":  "VGK",   # Vegas Golden Knights
    "UTH":  "UTA",   # Utah Mammoth (alt abbrev)
    "PHX":  "ARI",   # legacy Arizona
    "ANH":  "ANA",   # legacy Anaheim
}

# Fenwick = unblocked shot attempts; Corsi = all shot attempts
# MoneyPuck column names (with fallback aliases)
TEAM_COLS = {
    "xGF":      ["xGoalsFor"],
    "xGA":      ["xGoalsAgainst"],
    "GF":       ["goalsFor"],
    "GA":       ["goalsAgainst"],
    "fenw_for": ["unblockedShotAttemptsFor",  "fenwickForCount",  "fenwFor"],
    "fenw_aga": ["unblockedShotAttemptsAgainst", "fenwickAgainstCount", "fenwAgainst"],
    "corsi_for":["shotAttemptsFor",  "corsiForCount",  "corsiFor"],
    "corsi_aga":["shotAttemptsAgainst", "corsiAgainstCount", "corsiAgainst"],
    "icetime":  ["icetime", "iceTime", "toi"],
    "games":    ["games"],
}

GOALIE_COLS = {
    "xGA":   ["xGoals"],
    "GA":    ["goals"],
    "ongoal":["ongoal"],
    "games": ["games"],
    "name":  ["name"],
    "team":  ["team"],
}


def normalize_team(raw: str) -> str:
    s = str(raw).strip()
    return TEAM_NORM.get(s, s)


def col(df: pd.DataFrame, aliases: list, default=0):
    """Return first matching column value (Series), or default Series."""
    for a in aliases:
        if a in df.columns:
            return df[a]
    return pd.Series([default] * len(df), index=df.index)


def fetch_csv(url: str) -> pd.DataFrame:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text))


def build_team_metrics(df_all: pd.DataFrame) -> dict:
    all_sit  = df_all[df_all["situation"] == "all"].copy()
    fivev5   = df_all[df_all["situation"] == "5on5"].copy()

    metrics = {}
    for _, row in all_sit.iterrows():
        team = normalize_team(row.get("team", ""))
        if not team or team == "nan":
            continue

        # 5v5 row for Fenwick / Corsi
        f5 = fivev5[fivev5["team"] == row.get("team")]
        f5r = f5.iloc[0] if not f5.empty else None

        def v(aliases, r=row):
            for a in aliases:
                if a in r.index:
                    return float(r[a]) if pd.notna(r[a]) else 0.0
            return 0.0

        xgf = v(TEAM_COLS["xGF"])
        xga = v(TEAM_COLS["xGA"])
        gf  = v(TEAM_COLS["GF"])
        ga  = v(TEAM_COLS["GA"])
        ice = v(TEAM_COLS["icetime"])
        gms = int(v(TEAM_COLS["games"]))

        def f5v(aliases):
            if f5r is None:
                return 0.0
            for a in aliases:
                if a in f5r.index:
                    return float(f5r[a]) if pd.notna(f5r[a]) else 0.0
            return 0.0

        ff  = f5v(TEAM_COLS["fenw_for"])
        fa  = f5v(TEAM_COLS["fenw_aga"])
        cf  = f5v(TEAM_COLS["corsi_for"])
        ca  = f5v(TEAM_COLS["corsi_aga"])

        metrics[team] = {
            "xGF":         round(xgf, 2),
            "xGA":         round(xga, 2),
            "xGF_pct":     round(xgf / (xgf + xga) * 100, 1) if (xgf + xga) > 0 else 0,
            "GF":          int(gf),
            "GA":          int(ga),
            "pace_gf60":   round(gf / max(ice / 3600, 0.1), 2) if ice > 0 else None,
            "fenwick_pct": round(ff / (ff + fa) * 100, 1) if (ff + fa) > 0 else None,
            "corsi_pct":   round(cf / (cf + ca) * 100, 1) if (cf + ca) > 0 else None,
            "games":       gms,
        }
    return metrics


def tier_goalie(sv: float) -> str:
    if sv >= 0.920: return "ELITE"
    if sv >= 0.905: return "STRONG"
    if sv >= 0.895: return "AVG"
    return "WEAK"


def signal(sv: float) -> str:
    if sv >= 0.920: return "SUPPRESS"
    if sv >= 0.905: return "MILD_SUPPRESS"
    if sv >= 0.895: return "NEUTRAL"
    return "BOOST"


def build_playoff_goalie_map(df: pd.DataFrame) -> dict:
    """
    Build {team: {sv_pct, gsax, games}} from MoneyPuck playoff goalie CSV.
    Same structure as season data — xGoals, goals, ongoal columns.
    Returns empty dict if data unavailable or all teams have 0 games.
    """
    if "situation" in df.columns:
        df = df[df["situation"] == "all"].copy()

    result = {}
    for _, row in df.iterrows():
        team = normalize_team(row.get("team", ""))
        if not team or team == "nan":
            continue

        def v(aliases):
            for a in aliases:
                if a in row.index:
                    return float(row[a]) if pd.notna(row[a]) else 0.0
            return 0.0

        xga    = v(GOALIE_COLS["xGA"])
        ga     = v(GOALIE_COLS["GA"])
        ongoal = v(GOALIE_COLS["ongoal"])
        games  = int(v(GOALIE_COLS["games"]))

        if games == 0 or ongoal == 0:
            continue

        gsax   = round(ga - xga, 2)
        sv_pct = round(1 - ga / ongoal, 3)

        # Keep best-performing goalie per team (primary starter proxy)
        if team in result and result[team]["gsax"] <= gsax:
            continue

        result[team] = {"sv_pct": sv_pct, "gsax": gsax, "games": games}

    return result


def build_playoff_goalie_map_hockeyref(url: str) -> dict:
    """
    Fetch playoff goalie stats from Hockey-Reference using pd.read_html.
    Updates daily (~5:40 AM after games) — used as the primary playoff source.

    Returns {team_abbr: {sv_pct, gsax, games}} where gsax is always None
    (Hockey-Reference doesn't publish expected goals / GSAx).
    Returns empty dict on any fetch or parse failure.
    """
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; NHL-Linemate-Tracker/1.0)"},
        timeout=20,
    )
    resp.raise_for_status()

    # Parse with BeautifulSoup + stdlib html.parser — no lxml or html5lib required.
    try:
        from bs4 import BeautifulSoup, Comment
    except ImportError:
        raise RuntimeError("BeautifulSoup4 not installed. Run: pip install beautifulsoup4")

    soup = BeautifulSoup(resp.text, "html.parser")

    # HR buries most stats tables inside HTML comments to deter scrapers.
    # Count visible tables first (for debugging), then check comments.
    visible_tables = soup.find_all("table")
    print(f"    [HR debug] {len(visible_tables)} visible table(s); checking comments too")

    def _find_hr_stats_table(search_soup):
        """Return (table_tag, source_label) for the first table with Tm + SV% headers."""
        for tid in ("stats", "goalies"):
            t = search_soup.find("table", id=tid)
            if t:
                headers = [th.get_text(strip=True) for th in t.find_all("th")]
                if "SV%" in headers and any(h in ("Tm", "Team") for h in headers):
                    return t, f"id={tid!r}"
        for t in search_soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in t.find_all("th")]
            if "SV%" in headers and any(h in ("Tm", "Team") for h in headers):
                return t, "column-match"
        return None, None

    table, source = _find_hr_stats_table(soup)

    if table is None:
        # Check every HTML comment block for a hidden stats table
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            if "SV%" not in str(comment):
                continue
            comment_soup = BeautifulSoup(str(comment), "html.parser")
            table, source = _find_hr_stats_table(comment_soup)
            if table is not None:
                source = f"comment/{source}"
                break

    if table is None:
        print("    [HR debug] stats table not found — returning empty")
        return {}

    print(f"    [HR debug] using table ({source})")

    # Resolve column indices from the last header row
    thead = table.find("thead")
    header_row = thead.find_all("tr")[-1] if thead else None
    if header_row is None:
        return {}
    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

    tm_idx = next((i for i, h in enumerate(headers) if h in ("Tm", "Team")), None)
    sv_idx = next((i for i, h in enumerate(headers) if h in ("SV%", "Sv%")), None)
    gp_idx = next((i for i, h in enumerate(headers) if h == "GP"), None)
    if tm_idx is None or sv_idx is None or gp_idx is None:
        print(f"    [HR debug] missing columns — Tm:{tm_idx} SV%:{sv_idx} GP:{gp_idx}")
        return {}

    # Parse body rows directly — skips repeated <th> header rows automatically
    tbody = table.find("tbody") or table

    result = {}
    for row in tbody.find_all("tr"):
        cells = row.find_all(["td", "th"])
        # Skip header rows (all-th rows or rows too short)
        if not cells or cells[0].name == "th":
            continue
        if len(cells) <= max(tm_idx, sv_idx, gp_idx):
            continue

        team_raw = cells[tm_idx].get_text(strip=True)
        team = HOCKEYREF_TEAM_NORM.get(team_raw, team_raw)
        if not team or team in ("", "nan", "TOT", "Team", "Tm"):
            continue

        try:
            sv_pct = float(cells[sv_idx].get_text(strip=True))
        except (ValueError, TypeError):
            continue

        try:
            gp = int(float(cells[gp_idx].get_text(strip=True)))
        except (ValueError, TypeError):
            gp = 0

        if gp == 0 or sv_pct <= 0:
            continue

        # Keep the goalie with most GP per team (primary starter proxy)
        if team in result and result[team]["games"] >= gp:
            continue

        result[team] = {
            "sv_pct": round(sv_pct, 3),
            "gsax":   None,   # HR doesn't publish expected goals
            "games":  gp,
        }

    print(f"    [HR debug] parsed {len(result)} team(s): {sorted(result)}")
    return result


def parse_playoff_games(record_str: str) -> int:
    """Parse 'W-L-OT' DFO record string → total games played in current series."""
    try:
        return sum(int(p) for p in str(record_str).split("-") if p.strip().isdigit())
    except Exception:
        return 0


def _names_match(mp_name: str, confirmed_name: str) -> bool:
    """True if MoneyPuck name and confirmed starter name refer to the same player."""
    if not mp_name or not confirmed_name:
        return False

    def _norm(n: str) -> str:
        nfkd = unicodedata.normalize("NFKD", n.lower().strip())
        return nfkd.encode("ascii", "ignore").decode("ascii")

    return _norm(mp_name) == _norm(confirmed_name)


def build_goalie_metrics(df: pd.DataFrame,
                         playoff_games_map: dict | None = None,
                         playoff_sv_map: dict | None = None,
                         playoff_source: str = "moneypuck",
                         confirmed_starters: dict | None = None) -> dict:
    """
    Build per-team goalie metrics blending season and playoff data.

    playoff_games_map: {team: games_played_in_playoffs} from DFO W-L-OT record.
                       If absent for a team, falls back to 'games' in playoff_sv_map.
    playoff_sv_map:    {team: {sv_pct, gsax, games}} from any playoff source.
    playoff_source:    label stored in playoff_data_source field ("hockeyref" |
                       "moneypuck"). Ignored when falling back to season-only.

    Three blending cases (see playoff_data_source field in output):
      playoff_source  — playoff data available; full blend applied:
                        blended_sv = w * playoff_sv + (1-w) * season_sv
      "fallback"      — playoffs started (games > 0) but no data available;
                        blended_sv = season_sv; playoff_weight clamped to
                        PLAYOFF_FALLBACK_WEIGHT so the stored weight is honest
      "season_only"   — regular season or no games played; playoff_weight = 0.0
    tier() and signal() always use blended_sv; raw season stats also stored.
    """
    if "situation" in df.columns:
        df = df[df["situation"] == "all"].copy()

    if playoff_games_map is None:
        playoff_games_map = {}
    if playoff_sv_map is None:
        playoff_sv_map = {}
    if confirmed_starters is None:
        confirmed_starters = {}

    metrics = {}
    for _, row in df.iterrows():
        team = normalize_team(row.get("team", ""))
        if not team or team == "nan":
            continue

        def v(aliases):
            for a in aliases:
                if a in row.index:
                    return float(row[a]) if pd.notna(row[a]) else 0.0
            return 0.0

        name_val = str(row["name"]) if "name" in row.index and pd.notna(row["name"]) else ""

        xga    = v(GOALIE_COLS["xGA"])
        ga     = v(GOALIE_COLS["GA"])
        ongoal = v(GOALIE_COLS["ongoal"])
        season_gsax = round(ga - xga, 2)      # positive = worse than expected
        season_sv   = round(1 - ga / ongoal, 3) if ongoal > 0 else 0.0

        # Select the correct goalie per team
        if team in confirmed_starters:
            # Skip any row that isn't the confirmed starter — ignores backups entirely
            if not _names_match(name_val, confirmed_starters[team].get("name", "")):
                continue
        else:
            # No confirmed starter available: fall back to GSAx proxy
            if team in metrics and metrics[team]["season_gsax"] <= season_gsax:
                continue

        p_stats      = playoff_sv_map.get(team, {})
        playoff_sv   = p_stats.get("sv_pct")   # None if no playoff data yet
        playoff_gsax = p_stats.get("gsax")     # None for Hockey-Reference source

        playoff_games = playoff_games_map.get(team, 0)
        # If DFO record wasn't provided, use GP from the playoff source itself
        if playoff_games == 0 and p_stats:
            playoff_games = p_stats.get("games", 0)

        playoff_weight = get_playoff_goalie_weight(playoff_games)
        season_weight  = 1.0 - playoff_weight

        if playoff_sv is not None and playoff_games > 0:
            # Case 1: full blend — playoff data available (hockeyref or moneypuck)
            blended_sv   = round(playoff_sv   * playoff_weight + season_sv   * season_weight, 3)
            blended_gsax = round(playoff_gsax * playoff_weight + season_gsax * season_weight, 2) \
                           if playoff_gsax is not None else season_gsax
            data_source  = playoff_source
        elif playoff_games > 0:
            # Case 2: fallback — playoffs started but MoneyPuck CSV not yet populated.
            # blended_sv stays at season_sv; we clamp playoff_weight to PLAYOFF_FALLBACK_WEIGHT
            # so the stored weight honestly reflects "minimal playoff adjustment" rather than
            # claiming the full game-based weight (e.g. 0.40) when no playoff data was blended.
            playoff_weight = PLAYOFF_FALLBACK_WEIGHT
            blended_sv     = season_sv
            blended_gsax   = season_gsax
            data_source    = "fallback"
        else:
            # Case 3: regular season — no playoff games played
            blended_sv   = season_sv
            blended_gsax = season_gsax
            data_source  = "season_only"

        metrics[team] = {
            "name":               name_val,
            "season_sv":          season_sv,
            "season_gsax":        season_gsax,
            "playoff_sv":         playoff_sv,
            "playoff_gsax":       playoff_gsax,
            "playoff_games":      playoff_games,
            "playoff_weight":     playoff_weight,
            "playoff_data_source":data_source,
            "blended_sv":         blended_sv,
            "blended_gsax":       blended_gsax,
            "tier":               tier_goalie(blended_sv),
            "signal":             signal(blended_sv),
            "xGA":                round(xga, 2),
            "GA":                 int(ga),
            "games":              int(v(GOALIE_COLS["games"])),
            # Legacy aliases kept so existing callers that read sv_pct / GSAx still work
            "sv_pct":             season_sv,
            "GSAx":               season_gsax,
        }
    # Synthesise entries for confirmed starters that had no matching MoneyPuck row
    for team, starter_info in confirmed_starters.items():
        if team in metrics:
            continue
        starter_name = starter_info.get("name", "")
        try:
            season_sv = float(starter_info.get("svpct", 0.900))
        except (ValueError, TypeError):
            season_sv = 0.900

        playoff_games = playoff_games_map.get(team, 0)
        if playoff_games == 0:
            playoff_games = playoff_sv_map.get(team, {}).get("games", 0)
        playoff_weight = get_playoff_goalie_weight(playoff_games)
        season_weight  = 1.0 - playoff_weight

        p_stats      = playoff_sv_map.get(team, {})
        playoff_sv   = p_stats.get("sv_pct")
        playoff_gsax = p_stats.get("gsax")

        if playoff_sv is not None and playoff_games > 0:
            blended_sv   = round(playoff_sv * playoff_weight + season_sv * season_weight, 3)
            blended_gsax = None
            data_source  = playoff_source
        elif playoff_games > 0:
            playoff_weight = PLAYOFF_FALLBACK_WEIGHT
            blended_sv     = season_sv
            blended_gsax   = None
            data_source    = "fallback"
        else:
            blended_sv   = season_sv
            blended_gsax = None
            data_source  = "season_only"

        print(f"    [goalie] {team}: {starter_name!r} not in MoneyPuck — "
              f"using goalies.json sv_pct={season_sv}")
        metrics[team] = {
            "name":                starter_name,
            "season_sv":           season_sv,
            "season_gsax":         None,
            "playoff_sv":          playoff_sv,
            "playoff_gsax":        playoff_gsax,
            "playoff_games":       playoff_games,
            "playoff_weight":      playoff_weight,
            "playoff_data_source": data_source,
            "blended_sv":          blended_sv,
            "blended_gsax":        blended_gsax,
            "tier":                tier_goalie(blended_sv),
            "signal":              signal(blended_sv),
            "xGA":                 None,
            "GA":                  None,
            "games":               None,
            "sv_pct":              season_sv,
            "GSAx":                None,
            "source":              "goalies_json_fallback",
        }

    return metrics


def main():
    p = argparse.ArgumentParser(description="Fetch MoneyPuck advanced metrics")
    p.add_argument("--date",        default=datetime.now().strftime("%Y-%m-%d"),
                   help="Output date label YYYY-MM-DD")
    p.add_argument("--season",      default=2025, type=int,
                   help="Season start year (2025 = 2025-26 season)")
    p.add_argument("--goalies-json", default=None,
                   help="Path to goalies_DATE.json (enables dynamic playoff weight)")
    p.add_argument("--print-only",  action="store_true",
                   help="Print JSON to stdout, do not write file")
    p.add_argument("--debug-cols",  action="store_true",
                   help="Print available CSV column names and exit")
    args = p.parse_args()

    team_url   = f"{BASE_URL.format(season=args.season)}/teams.csv"
    goalie_url = f"{BASE_URL.format(season=args.season)}/goalies.csv"

    if args.debug_cols:
        print("--- TEAM COLS ---")
        print(list(fetch_csv(team_url).columns))
        print("--- GOALIE COLS ---")
        print(list(fetch_csv(goalie_url).columns))
        return

    # Load goalies JSON: confirmed starters + playoff game counts
    playoff_games_map = {}
    confirmed_starters = {}
    if args.goalies_json:
        goalies_json_path = Path(args.goalies_json).expanduser()
        if not goalies_json_path.exists():
            print(f"  ⚠  WARNING: --goalies-json not found: {goalies_json_path}", flush=True)
            print(f"     Goalie selection will use MoneyPuck GSAx proxy — "
                  f"playoff_weight defaults to 0.0")
        else:
            try:
                with goalies_json_path.open(encoding="utf-8") as f:
                    goalies_data = json.load(f)
                for team, info in goalies_data.items():
                    playoff_games_map[team] = parse_playoff_games(info.get("record", "0-0-0"))
                    if info.get("goalie"):
                        confirmed_starters[team] = {
                            "name":  info["goalie"],
                            "svpct": info.get("svpct", "0.900"),
                        }
                print(f"  → goalies.json loaded: {len(confirmed_starters)} confirmed starters, "
                      f"{sum(v > 0 for v in playoff_games_map.values())} teams with playoff games")
            except Exception as e:
                print(f"  ⚠  WARNING: --goalies-json load failed: {e}", flush=True)
                print(f"     Goalie selection will use MoneyPuck GSAx proxy — "
                      f"playoff_weight defaults to 0.0")

    teams, goalies = {}, {}
    playoff_sv_map = {}
    playoff_source = "moneypuck"  # updated to "hockeyref" if HR succeeds

    print(f"Fetching MoneyPuck advanced metrics (season {args.season}-{args.season + 1})...")

    try:
        print("  → team stats ... ", end="", flush=True)
        df_teams = fetch_csv(team_url)
        teams = build_team_metrics(df_teams)
        print(f"{len(teams)} teams")
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)

    # ── Playoff goalie stats: try Hockey-Reference first, then MoneyPuck ────────
    # Step 1: Hockey-Reference (primary — updates daily, usually by ~5:40 AM)
    print("  → playoff goalie stats (Hockey-Reference) ... ", end="", flush=True)
    try:
        hr_year = args.season + 1
        hr_map = build_playoff_goalie_map_hockeyref(
            HOCKEYREF_PLAYOFF_URL.format(year=hr_year)
        )
        if hr_map:
            playoff_sv_map = hr_map
            playoff_source = "hockeyref"
            print(f"{len(hr_map)} teams")
        else:
            print("0 teams (page empty or not yet updated)")
    except Exception as e:
        print(f"unavailable ({e})")

    # Step 2: MoneyPuck fallback if HR gave nothing
    if not playoff_sv_map:
        print("  → playoff goalie stats (MoneyPuck fallback) ... ", end="", flush=True)
        try:
            df_playoff = fetch_csv(
                f"{PLAYOFF_BASE_URL.format(season=args.season)}/goalies.csv"
            )
            mp_map = build_playoff_goalie_map(df_playoff)
            if mp_map:
                playoff_sv_map = mp_map
                playoff_source = "moneypuck"
                print(f"{len(mp_map)} teams")
            else:
                games_in_progress = sum(1 for g in playoff_games_map.values() if g > 0)
                print(f"0 teams — CSV empty. "
                      f"Fallback weight {PLAYOFF_FALLBACK_WEIGHT} applied to "
                      f"{games_in_progress} team(s) with games played.")
        except Exception as e:
            games_in_progress = sum(1 for g in playoff_games_map.values() if g > 0)
            print(f"unavailable — fallback weight {PLAYOFF_FALLBACK_WEIGHT} applied to "
                  f"{games_in_progress} team(s). ({e})")
    # ────────────────────────────────────────────────────────────────────────────

    try:
        print("  → season goalie stats ... ", end="", flush=True)
        df_goalies = fetch_csv(goalie_url)
        goalies = build_goalie_metrics(
            df_goalies,
            playoff_games_map=playoff_games_map,
            playoff_sv_map=playoff_sv_map,
            playoff_source=playoff_source,
            confirmed_starters=confirmed_starters,
        )
        print(f"{len(goalies)} goalies")
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)

    output = {
        "date":    args.date,
        "season":  f"{args.season}-{args.season + 1}",
        "fetched": datetime.now().isoformat(),
        "teams":   teams,
        "goalies": goalies,
    }

    if args.print_only:
        print(json.dumps(output, indent=2))
        return

    out_path = f"data/advanced_metrics_{args.date}.json"
    os.makedirs("data", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n✅  {out_path}  ({len(teams)} teams · {len(goalies)} goalies)")


if __name__ == "__main__":
    main()