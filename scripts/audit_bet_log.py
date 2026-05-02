#!/usr/bin/env python3
"""
audit_bet_log.py — Scan data/bet_log.csv for null/empty fields per row.

Usage:
    py scripts/audit_bet_log.py
    py scripts/audit_bet_log.py --date 2026-04-29
    py scripts/audit_bet_log.py --date 2026-04-29 --verbose
    py scripts/audit_bet_log.py --verbose

Exit code: 0 = no gaps found, 1 = gaps found (useful for CI checks).
"""

import argparse
import csv
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BET_LOG  = DATA_DIR / "bet_log.csv"

REQUIRED_FIELDS = [
    "date", "bet_description", "signal_tier", "stake_units",
    "price_taken", "book", "closing_line", "clv_cents", "result", "pnl_units",
]


def load_rows(path=BET_LOG, date_filter=None):
    if not path.exists():
        print(f"ERROR: {path} not found.")
        sys.exit(1)
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if date_filter:
        rows = [r for r in rows if r.get("date", "").strip() == date_filter]
    return rows


def audit_rows(rows):
    """Return list of (csv_line_num, row, [missing_fields]) for rows with gaps."""
    gaps = []
    for i, row in enumerate(rows, start=2):  # 2 = 1-indexed + skip header row
        missing = [f for f in REQUIRED_FIELDS if not row.get(f, "").strip()]
        if missing:
            gaps.append((i, row, missing))
    return gaps


def report(rows, gaps, date_filter=None, verbose=False):
    n = len(rows)
    label = f"date={date_filter}" if date_filter else "all dates"

    if n == 0:
        print(f"\nNo rows found ({label}).")
        return

    field_counts = {f: 0 for f in REQUIRED_FIELDS}
    for _, _, missing in gaps:
        for f in missing:
            field_counts[f] += 1

    print(f"\n{'─'*56}")
    print(f"  BET LOG AUDIT  ({label})")
    print(f"{'─'*56}")
    print(f"  Rows scanned  : {n}")
    print(f"  Rows with gaps: {len(gaps)}")
    print(f"  Complete rows : {n - len(gaps)}")
    print()

    any_gap = False
    for f in REQUIRED_FIELDS:
        count = field_counts[f]
        if count:
            any_gap = True
            pct = 100 * count // n
            print(f"  {f:<20}  {count:3d} gap(s)  ({pct:3d}%)")

    if not any_gap:
        print("  ✅ No gaps — all required fields populated in every row.")

    if verbose and gaps:
        print(f"\n{'─'*56}")
        print(f"  GAP DETAIL")
        print(f"{'─'*56}")
        for line_num, row, missing in gaps:
            date = row.get("date", "?")
            desc = (row.get("bet_description", "") or "")[:40]
            print(f"  row {line_num:4d}  {date}  {desc!r}")
            for f in missing:
                print(f"             ↳ {f}  EMPTY/NULL")

    print(f"{'─'*56}\n")


def main():
    parser = argparse.ArgumentParser(description="Audit bet_log.csv for missing fields")
    parser.add_argument("--date",    help="Filter to a single date (YYYY-MM-DD)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show per-row gap detail")
    args = parser.parse_args()

    rows = load_rows(date_filter=args.date)
    gaps = audit_rows(rows)
    report(rows, gaps, date_filter=args.date, verbose=args.verbose)
    sys.exit(1 if gaps else 0)


if __name__ == "__main__":
    main()
