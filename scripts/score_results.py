#!/usr/bin/env python3
"""
score_results.py — Post-game signal scorer
Joins cold sticks and hot player chain predictions against actual goal chains.
Appends one row per prediction to data/results_log.csv.

Usage:
    py scripts/score_results.py --date 2026-04-21
    py scripts/score_results.py --backfill          # score all past dates with both files
    py scripts/score_results.py --date 2026-04-21 --dry-run
    py scripts/score_results.py --summary           # print cumulative stats from log
"""

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_LOG = DATA_DIR / "results_log.csv"

CSV_FIELDS = [
    "date", "type", "player", "team", "duo_tier",
    "blanks", "l5_pts", "result", "break_type", "chain_detail",
]


# ── helpers ──────────────────────────────────────────────────────────────────

def load_json(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_chain_lookup(chains_data):
    """
    active_players : name → list of goal dicts they appeared in
    chain_pairs    : frozenset({name1, name2}) → first goal dict where both appear
    """
    active = defaultdict(list)
    pairs = {}
    for goal in chains_data.get("goals", []):
        chain = [p for p in goal.get("chain", []) if p]
        for player in chain:
            active[player].append(goal)
        for i in range(len(chain)):
            for j in range(i + 1, len(chain)):
                key = frozenset({chain[i], chain[j]})
                if key not in pairs:
                    pairs[key] = goal
    return active, pairs


def goal_label(goal):
    return f"{goal['game']} P{goal['period']} {goal['time']} {goal['strength']}"


# ── cold stick scoring ────────────────────────────────────────────────────────

def score_cold_sticks(verified, active_players, date):
    rows = []
    for cs in verified.get("cold_sticks", []):
        name   = cs["name"]
        team   = cs["team"]
        tier   = cs["tier"]
        blanks = cs["blanks"]
        l5_pts = cs["l5_pts"]

        if name in active_players:
            appearances = active_players[name]
            scored = any(g["scorer"] == name for g in appearances)
            break_type   = "goal" if scored else "assist"
            chain_detail = goal_label(appearances[0])
            result = "L"
        else:
            break_type   = "none"
            chain_detail = ""
            result = "W"

        rows.append({
            "date": date, "type": f"cold_stick_{tier}",
            "player": name, "team": team, "duo_tier": tier,
            "blanks": blanks, "l5_pts": l5_pts,
            "result": result, "break_type": break_type,
            "chain_detail": chain_detail,
        })
    return rows


# ── hot duo chain scoring ─────────────────────────────────────────────────────

def get_lineup_aware_pairs(lineups_data, hot_names_by_team):
    """
    Yield (p1, p2, team, duo_tier) only for hot player pairs that share
    an ES line or PP unit in tonight's lineup — matching the duo generation logic.
    """
    for team, slots in (lineups_data or {}).items():
        if not isinstance(slots, dict):
            continue
        hot = hot_names_by_team.get(team, [])
        if len(hot) < 2:
            continue

        es_line = {}   # player → line label (L1…L4)
        for line in ("L1", "L2", "L3", "L4"):
            for p in slots.get(line, []):
                es_line[p] = line

        pp_unit = {}   # player → PP label (PP1, PP2)
        for pp in ("PP1", "PP2"):
            for p in slots.get(pp, []):
                pp_unit[p] = pp

        for i in range(len(hot)):
            for j in range(i + 1, len(hot)):
                p1, p2 = hot[i], hot[j]
                same_es = es_line.get(p1) and es_line.get(p1) == es_line.get(p2)
                same_pp = pp_unit.get(p1) and pp_unit.get(p1) == pp_unit.get(p2)
                if not same_es and not same_pp:
                    continue  # not a valid duo
                if same_es and same_pp and pp_unit.get(p1) == "PP1":
                    tier = "ELITE"
                elif same_es and same_pp:
                    tier = "ELITE_PP2"
                elif same_pp:
                    tier = "PP_LINK"
                else:
                    tier = "STRONG"
                yield p1, p2, team, tier


def score_hot_chains(verified, active_players, chain_pairs, lineups_data, date):
    hot = verified.get("hot_players", [])
    hot_by_name = {p["name"]: p for p in hot}

    # Group hot player names by team
    hot_names_by_team = defaultdict(list)
    for p in hot:
        hot_names_by_team[p["team"]].append(p["name"])

    rows = []
    for p1, p2, team, tier in get_lineup_aware_pairs(lineups_data, hot_names_by_team):
        p1_l5 = hot_by_name[p1]["l5_pts"]
        p2_l5 = hot_by_name[p2]["l5_pts"]
        key = frozenset({p1, p2})

        if key in chain_pairs:
            goal = chain_pairs[key]
            result       = "W"
            break_type   = "chain_overlap"
            chain_detail = goal_label(goal)
        else:
            both_active  = p1 in active_players and p2 in active_players
            result       = "L"
            break_type   = "both_active_no_chain" if both_active else "no_chain_overlap"
            chain_detail = ""

        rows.append({
            "date": date, "type": f"hot_duo_{tier}",
            "player": f"{p1} + {p2}", "team": team, "duo_tier": tier,
            "blanks": "", "l5_pts": f"{p1_l5}+{p2_l5}",
            "result": result, "break_type": break_type,
            "chain_detail": chain_detail,
        })
    return rows


# ── CSV I/O ───────────────────────────────────────────────────────────────────

def already_scored(date):
    if not RESULTS_LOG.exists():
        return False
    with open(RESULTS_LOG, newline="", encoding="utf-8") as f:
        return any(row["date"] == date for row in csv.DictReader(f))


def append_to_log(rows):
    write_header = not RESULTS_LOG.exists()
    with open(RESULTS_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


# ── per-date orchestration ────────────────────────────────────────────────────

def wr_str(lst):
    if not lst:
        return "  —"
    w = sum(1 for r in lst if r["result"] == "W")
    pct = 100 * w // len(lst)
    return f"{w:2d}/{len(lst):2d} ({pct:3d}%)"


def score_date(date_str, dry_run=False, verbose=True):
    verified = load_json(DATA_DIR / f"verified_{date_str}.json")
    chains   = load_json(DATA_DIR / f"chains_{date_str}.json")
    lineups  = load_json(DATA_DIR / f"lineups_{date_str}.json")

    if not verified:
        if verbose:
            print(f"  ⚠  No verified_{date_str}.json — skip")
        return 0
    if not chains:
        if verbose:
            print(f"  ⚠  No chains_{date_str}.json  — skip")
        return 0

    active_players, chain_pairs = build_chain_lookup(chains)
    cold_rows = score_cold_sticks(verified, active_players, date_str)
    hot_rows  = score_hot_chains(verified, active_players, chain_pairs, lineups, date_str)
    all_rows  = cold_rows + hot_rows

    if verbose:
        cold_a = [r for r in cold_rows if r["duo_tier"] == "A"]
        cold_b = [r for r in cold_rows if r["duo_tier"] == "B"]
        elite  = [r for r in hot_rows  if r["duo_tier"] == "ELITE"]
        strong = [r for r in hot_rows  if r["duo_tier"] == "STRONG"]
        pp     = [r for r in hot_rows  if "PP_LINK" in r["duo_tier"]]

        print(f"\n  📊 {date_str}")
        print(f"     Cold Stick A : {wr_str(cold_a)}")
        print(f"     Cold Stick B : {wr_str(cold_b)}")
        print(f"     Hot ELITE duo: {wr_str(elite)}")
        print(f"     Hot STRONG   : {wr_str(strong)}")
        print(f"     Hot PP LINK  : {wr_str(pp)}")

        breaks = [r for r in cold_rows if r["result"] == "L"]
        for b in breaks:
            print(f"     ❌ {b['player']} ({b['team']}) [Tier {b['duo_tier']}] "
                  f"broke via {b['break_type']} — {b['chain_detail']}")

    if not dry_run:
        append_to_log(all_rows)

    return len(all_rows)


# ── summary report ────────────────────────────────────────────────────────────

def print_summary():
    if not RESULTS_LOG.exists():
        print("No results_log.csv yet. Run with --date or --backfill first.")
        return

    with open(RESULTS_LOG, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("results_log.csv is empty.")
        return

    buckets = defaultdict(list)
    for r in rows:
        buckets[r["type"]].append(r)

    print(f"\n{'─'*55}")
    print(f"  RESULTS LOG SUMMARY  ({rows[0]['date']} → {rows[-1]['date']})")
    print(f"{'─'*55}")
    for key in sorted(buckets):
        lst = buckets[key]
        w   = sum(1 for r in lst if r["result"] == "W")
        pct = 100 * w // len(lst)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"  {key:<28s} {w:3d}/{len(lst):3d}  {pct:3d}%  {bar}")
    print(f"{'─'*55}")
    total_w = sum(1 for r in rows if r["result"] == "W")
    print(f"  {'TOTAL':<28s} {total_w:3d}/{len(rows):3d}  {100*total_w//len(rows):3d}%")
    print(f"{'─'*55}\n")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Score post-game predictions vs actual chains")
    parser.add_argument("--date",     help="Date to score (YYYY-MM-DD); defaults to yesterday")
    parser.add_argument("--backfill", action="store_true", help="Score all past dates with both files present")
    parser.add_argument("--dry-run",  action="store_true", help="Print results without writing CSV")
    parser.add_argument("--summary",  action="store_true", help="Print cumulative summary from results_log.csv")
    args = parser.parse_args()

    if args.summary:
        print_summary()
        return

    if args.backfill:
        verified_dates = {f.stem[len("verified_"):] for f in DATA_DIR.glob("verified_*.json")}
        chains_dates   = {f.stem[len("chains_"):  ] for f in DATA_DIR.glob("chains_*.json")}
        scoreable = sorted(verified_dates & chains_dates)

        print(f"🔄 Backfill — {len(scoreable)} dates: {', '.join(scoreable)}")
        if not args.dry_run:
            already = {d for d in scoreable if already_scored(d)}
            if already:
                print(f"   Skipping already-scored: {', '.join(sorted(already))}")
            scoreable = [d for d in scoreable if d not in already]

        total = 0
        for d in scoreable:
            total += score_date(d, dry_run=args.dry_run)

        action = "would write" if args.dry_run else "wrote"
        print(f"\n✅ Backfill complete — {action} {total} rows")
        if not args.dry_run:
            print_summary()
        return

    date = args.date or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"🏒 Scoring {date}")

    if not args.dry_run and already_scored(date):
        print(f"  ⚠  {date} already in results_log.csv. Use --dry-run to preview or delete the rows to re-score.")
        return

    n = score_date(date, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"\n✅ {n} rows appended → {RESULTS_LOG}")
        print_summary()


if __name__ == "__main__":
    main()
