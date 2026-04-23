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

BASE_URL = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{season}/regular"
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


def build_goalie_metrics(df: pd.DataFrame) -> dict:
    if "situation" in df.columns:
        df = df[df["situation"] == "all"].copy()

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
        gsax   = round(ga - xga, 2)          # positive = worse than expected
        sv_pct = round(1 - ga / ongoal, 3) if ongoal > 0 else 0.0

        # Keep best-performing goalie per team (most negative goals-xGoals = primary starter proxy)
        if team in metrics and metrics[team]["GSAx"] <= gsax:
            continue

        metrics[team] = {
            "name":   name_val,
            "GSAx":   gsax,
            "xGA":    round(xga, 2),
            "GA":     int(ga),
            "sv_pct": sv_pct,
            "tier":   tier_goalie(sv_pct),
            "signal": signal(sv_pct),
            "games":  int(v(GOALIE_COLS["games"])),
        }
    return metrics


def main():
    p = argparse.ArgumentParser(description="Fetch MoneyPuck advanced metrics")
    p.add_argument("--date",       default=datetime.now().strftime("%Y-%m-%d"),
                   help="Output date label YYYY-MM-DD")
    p.add_argument("--season",     default=2025, type=int,
                   help="Season start year (2025 = 2025-26 season)")
    p.add_argument("--print-only", action="store_true",
                   help="Print JSON to stdout, do not write file")
    p.add_argument("--debug-cols", action="store_true",
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

    teams, goalies = {}, {}

    print(f"Fetching MoneyPuck advanced metrics (season {args.season}-{args.season + 1})...")

    try:
        print("  → team stats ... ", end="", flush=True)
        df_teams = fetch_csv(team_url)
        teams = build_team_metrics(df_teams)
        print(f"{len(teams)} teams")
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)

    try:
        print("  → goalie stats ... ", end="", flush=True)
        df_goalies = fetch_csv(goalie_url)
        goalies = build_goalie_metrics(df_goalies)
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
