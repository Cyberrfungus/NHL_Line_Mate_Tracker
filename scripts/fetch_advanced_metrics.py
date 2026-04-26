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
from datetime import datetime
from io import StringIO

import requests
import pandas as pd

try:
    from scripts.utils import get_playoff_goalie_weight
except ImportError:
    from utils import get_playoff_goalie_weight

BASE_URL             = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{season}/regular"
PLAYOFF_BASE_URL     = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{season}/playoffs"
# Applied when playoffs are underway but MoneyPuck's playoff CSV hasn't populated yet.
# Signals "playoff mode, low confidence" without misrepresenting the blend ratio.
PLAYOFF_FALLBACK_WEIGHT = 0.10
HEADERS = {"User-Agent": "NHL-Line-Mate-Tracker/1.0"}

# MoneyPuck abbrevs that differ from project standard
TEAM_NORM = {
    "T.B": "TBL", "N.J": "NJD", "S.J": "SJS", "L.A": "LAK",
    "T.B.": "TBL", "N.J.": "NJD", "S.J.": "SJS", "L.A.": "LAK",
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


def parse_playoff_games(record_str: str) -> int:
    """Parse 'W-L-OT' DFO record string → total games played in current series."""
    try:
        return sum(int(p) for p in str(record_str).split("-") if p.strip().isdigit())
    except Exception:
        return 0


def build_goalie_metrics(df: pd.DataFrame,
                         playoff_games_map: dict | None = None,
                         playoff_sv_map: dict | None = None) -> dict:
    """
    Build per-team goalie metrics blending season and playoff data.

    playoff_games_map: {team: games_played_in_playoffs} from DFO record.
    playoff_sv_map:    {team: {sv_pct, gsax}} from MoneyPuck playoffs CSV.

    Three blending cases (see playoff_data_source field in output):
      "moneypuck"   — playoff CSV available; full blend applied:
                      blended_sv = w * playoff_sv + (1-w) * season_sv
      "fallback"    — playoffs started (games > 0) but CSV empty/unavailable;
                      blended_sv = season_sv; playoff_weight clamped to
                      PLAYOFF_FALLBACK_WEIGHT so the stored weight is honest
      "season_only" — regular season or no games played; blended_sv = season_sv,
                      playoff_weight = 0.0
    tier() and signal() always use blended_sv; raw season stats also stored.
    """
    if "situation" in df.columns:
        df = df[df["situation"] == "all"].copy()

    if playoff_games_map is None:
        playoff_games_map = {}
    if playoff_sv_map is None:
        playoff_sv_map = {}

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

        # Keep best-performing goalie per team (most negative GSAx = primary starter proxy)
        if team in metrics and metrics[team]["season_gsax"] <= season_gsax:
            continue

        playoff_games  = playoff_games_map.get(team, 0)
        playoff_weight = get_playoff_goalie_weight(playoff_games)
        season_weight  = 1.0 - playoff_weight

        p_stats      = playoff_sv_map.get(team, {})
        playoff_sv   = p_stats.get("sv_pct")   # None if no playoff data yet
        playoff_gsax = p_stats.get("gsax")

        if playoff_sv is not None and playoff_games > 0:
            # Case 1: full blend — MoneyPuck playoff data is available
            blended_sv   = round(playoff_sv   * playoff_weight + season_sv   * season_weight, 3)
            blended_gsax = round(playoff_gsax * playoff_weight + season_gsax * season_weight, 2) \
                           if playoff_gsax is not None else season_gsax
            data_source  = "moneypuck"
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

    # Load playoff game counts from goalies JSON if provided
    playoff_games_map = {}
    if args.goalies_json:
        try:
            with open(args.goalies_json, encoding="utf-8") as f:
                goalies_data = json.load(f)
            for team, info in goalies_data.items():
                playoff_games_map[team] = parse_playoff_games(info.get("record", "0-0-0"))
            print(f"  → playoff games loaded from {args.goalies_json}: "
                  f"{sum(v > 0 for v in playoff_games_map.values())} teams with games played")
        except Exception as e:
            print(f"  → goalies-json load failed ({e}), playoff_weight defaults to 0.0",
                  file=sys.stderr)

    teams, goalies = {}, {}
    playoff_sv_map = {}

    print(f"Fetching MoneyPuck advanced metrics (season {args.season}-{args.season + 1})...")

    try:
        print("  → team stats ... ", end="", flush=True)
        df_teams = fetch_csv(team_url)
        teams = build_team_metrics(df_teams)
        print(f"{len(teams)} teams")
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)

    try:
        print("  → playoff goalie stats ... ", end="", flush=True)
        df_playoff = fetch_csv(f"{PLAYOFF_BASE_URL.format(season=args.season)}/goalies.csv")
        playoff_sv_map = build_playoff_goalie_map(df_playoff)
        if playoff_sv_map:
            print(f"{len(playoff_sv_map)} teams with playoff data")
        else:
            # CSV fetched but contained no usable rows (MoneyPuck updates slowly early in series).
            # build_goalie_metrics will apply PLAYOFF_FALLBACK_WEIGHT for teams with games played.
            games_in_progress = sum(1 for g in playoff_games_map.values() if g > 0)
            print(f"0 teams — CSV empty (MoneyPuck not yet updated). "
                  f"Fallback weight {PLAYOFF_FALLBACK_WEIGHT} applied to "
                  f"{games_in_progress} team(s) with games played.")
    except Exception as e:
        games_in_progress = sum(1 for g in playoff_games_map.values() if g > 0)
        print(f"not available — fallback weight {PLAYOFF_FALLBACK_WEIGHT} applied to "
              f"{games_in_progress} team(s) with games played. ({e})")

    try:
        print("  → season goalie stats ... ", end="", flush=True)
        df_goalies = fetch_csv(goalie_url)
        goalies = build_goalie_metrics(
            df_goalies,
            playoff_games_map=playoff_games_map,
            playoff_sv_map=playoff_sv_map,
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
