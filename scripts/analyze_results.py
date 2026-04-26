#!/usr/bin/env python3
"""
analyze_results.py — Signal combination win-rate analysis
Reads data/results_log.csv and prints breakdown tables by signal type,
tier, blanks bucket, and l5_pts bucket.

Usage:
    py scripts/analyze_results.py
    py scripts/analyze_results.py --min-obs 10     # only show buckets with 10+ obs
    py scripts/analyze_results.py --cold           # cold sticks detail only
    py scripts/analyze_results.py --duos           # hot duo chains detail only
    py scripts/analyze_results.py --csv            # dump full breakdown to stdout as CSV
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

DATA_DIR  = Path(__file__).parent.parent / "data"
LOG_PATH  = DATA_DIR / "results_log.csv"


# ── formatting helpers ────────────────────────────────────────────────────────

def pct(w, n):
    return 0 if n == 0 else 100 * w // n

def bar(p, width=20):
    filled = round(p / 100 * width)
    return "█" * filled + "░" * (width - filled)

def wr_row(label, wins, total, width=32):
    p = pct(wins, total)
    return f"  {label:<{width}}  {wins:3d}/{total:3d}  {p:3d}%  {bar(p)}"

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ── data loading ──────────────────────────────────────────────────────────────

def load_rows():
    if not LOG_PATH.exists():
        print(f"No results log found at {LOG_PATH}. Run score_results.py first.")
        sys.exit(1)
    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def date_range(rows):
    dates = sorted({r["date"] for r in rows})
    return dates[0], dates[-1], len(dates)


# ── cold stick analysis ───────────────────────────────────────────────────────

def analyze_cold(rows, min_obs):
    cold = [r for r in rows if r["type"].startswith("cold_stick_")]
    if not cold:
        print("  No cold stick data.")
        return

    section(f"COLD STICKS  (n={len(cold)})")

    # By tier
    for tier in ("A", "B"):
        bucket = [r for r in cold if r["duo_tier"] == tier]
        if len(bucket) >= min_obs:
            w = sum(1 for r in bucket if r["result"] == "W")
            print(wr_row(f"Tier {tier}", w, len(bucket)))

    # Tier A by blanks bucket
    section("COLD STICK A — by consecutive blanks")
    tier_a = [r for r in cold if r["duo_tier"] == "A"]
    by_blanks = defaultdict(list)
    for r in tier_a:
        try:
            b = int(r["blanks"])
        except (ValueError, TypeError):
            continue
        by_blanks[b].append(r)
    for b in sorted(by_blanks):
        bucket = by_blanks[b]
        if len(bucket) >= min_obs:
            w = sum(1 for r in bucket if r["result"] == "W")
            print(wr_row(f"blanks = {b}", w, len(bucket)))

    # Tier A + B by l5_pts bucket
    section("COLD STICKS — by L5 pts total")
    by_pts = defaultdict(list)
    for r in cold:
        try:
            p = int(r["l5_pts"])
        except (ValueError, TypeError):
            continue
        label = "0 pts" if p == 0 else ("1 pt" if p == 1 else "2 pts" if p == 2 else "3+ pts")
        by_pts[label].append(r)
    for label in ("0 pts", "1 pt", "2 pts", "3+ pts"):
        bucket = by_pts.get(label, [])
        if len(bucket) >= min_obs:
            w = sum(1 for r in bucket if r["result"] == "W")
            print(wr_row(label, w, len(bucket)))

    # Break type distribution
    section("COLD STICK BREAKS — how they broke")
    breaks = [r for r in cold if r["result"] == "L"]
    by_break = defaultdict(int)
    for r in breaks:
        by_break[r["break_type"]] += 1
    total_b = len(breaks)
    if total_b:
        print(f"  Total breaks: {total_b} / {len(cold)}")
        for btype, count in sorted(by_break.items(), key=lambda x: -x[1]):
            print(f"    {btype:<25}  {count:3d}  ({100*count//total_b:3d}%)")


# ── hot duo chain analysis ────────────────────────────────────────────────────

def analyze_duos(rows, min_obs):
    duos = [r for r in rows if r["type"].startswith("hot_duo_")]
    if not duos:
        print("  No hot duo chain data.")
        return

    section(f"HOT DUO CHAIN OVERLAPS  (n={len(duos)})")

    # ELITE+PP2 vs ELITE (non-PP2) comparison — highest-signal breakdown
    elite_pp2  = [r for r in duos if r["duo_tier"] == "ELITE_PP2"]
    elite_only = [r for r in duos if r["duo_tier"] == "ELITE"]
    if elite_pp2:
        w = sum(1 for r in elite_pp2 if r["result"] == "W")
        print(wr_row("ELITE+PP2 (★ BEST TIER)", w, len(elite_pp2)))
    if elite_only:
        w = sum(1 for r in elite_only if r["result"] == "W")
        print(wr_row("ELITE (no PP2 share)", w, len(elite_only)))

    # By duo_tier (all tiers)
    tiers = sorted({r["duo_tier"] for r in duos})
    for t in tiers:
        if t in ("ELITE_PP2", "ELITE"):
            continue  # already printed above
        bucket = [r for r in duos if r["duo_tier"] == t]
        if len(bucket) >= min_obs:
            w = sum(1 for r in bucket if r["result"] == "W")
            print(wr_row(t, w, len(bucket)))

    # Chain overlap vs both-active-no-chain vs no-overlap
    section("HOT DUO — result breakdown (all tiers)")
    by_break = defaultdict(int)
    for r in duos:
        by_break[r["break_type"]] += 1
    total = len(duos)
    for btype, count in sorted(by_break.items(), key=lambda x: -x[1]):
        print(f"    {btype:<30}  {count:3d}  ({100*count//total:3d}%)")

    # ELITE+PP2 — chain overlap rate per date (trend check)
    section("HOT DUO ELITE+PP2 — chain overlap rate by date")
    by_date = defaultdict(list)
    for r in elite_pp2:
        by_date[r["date"]].append(r)
    for d in sorted(by_date):
        bucket = by_date[d]
        w = sum(1 for r in bucket if r["result"] == "W")
        print(wr_row(d, w, len(bucket), width=14))

    # Standard ELITE only — chain overlap rate per date (trend check)
    section("HOT DUO ELITE (no PP2) — chain overlap rate by date")
    by_date = defaultdict(list)
    for r in elite_only:
        by_date[r["date"]].append(r)
    for d in sorted(by_date):
        bucket = by_date[d]
        w = sum(1 for r in bucket if r["result"] == "W")
        print(wr_row(d, w, len(bucket), width=14))


# ── combined summary ──────────────────────────────────────────────────────────

def summary(rows, min_obs):
    d_from, d_to, n_dates = date_range(rows)
    section(f"OVERALL SUMMARY  ({d_from} → {d_to}, {n_dates} dates, {len(rows)} obs)")

    by_type = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r)

    for key in sorted(by_type):
        bucket = by_type[key]
        if len(bucket) >= min_obs:
            w = sum(1 for r in bucket if r["result"] == "W")
            print(wr_row(key, w, len(bucket)))

    total_w = sum(1 for r in rows if r["result"] == "W")
    print(f"\n  {'ALL ROWS':<32}  {total_w:3d}/{len(rows):3d}  {pct(total_w, len(rows)):3d}%")


# ── CSV dump ──────────────────────────────────────────────────────────────────

def dump_csv(rows):
    from collections import OrderedDict
    buckets = defaultdict(lambda: [0, 0])  # type → [wins, total]
    for r in rows:
        key = r["type"]
        buckets[key][1] += 1
        if r["result"] == "W":
            buckets[key][0] += 1
    writer = csv.writer(sys.stdout)
    writer.writerow(["type", "wins", "total", "pct"])
    for key in sorted(buckets):
        w, n = buckets[key]
        writer.writerow([key, w, n, pct(w, n)])


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Analyze results_log.csv signal win rates")
    parser.add_argument("--min-obs", type=int, default=5,
                        help="Minimum observations to show a bucket (default: 5)")
    parser.add_argument("--cold",  action="store_true", help="Cold sticks analysis only")
    parser.add_argument("--duos",  action="store_true", help="Hot duo chains analysis only")
    parser.add_argument("--csv",   action="store_true", help="Dump breakdown as CSV to stdout")
    args = parser.parse_args()

    rows = load_rows()

    if args.csv:
        dump_csv(rows)
        return

    summary(rows, args.min_obs)

    if args.cold or not args.duos:
        analyze_cold(rows, args.min_obs)

    if args.duos or not args.cold:
        analyze_duos(rows, args.min_obs)


if __name__ == "__main__":
    main()
