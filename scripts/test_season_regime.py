#!/usr/bin/env python3
"""
test_season_regime.py — Tests for season derivation and regime auto-detection
in scripts/utils.py. These guard the season-rollover logic so the pipeline
keeps working every October without manual edits.

Run: py scripts/test_season_regime.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import derive_season_start_year, derive_season_code, detect_regime

PASS = FAIL = 0

def check(label, actual, expected):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label} — expected {expected!r}, got {actual!r}")


# ── season start year ────────────────────────────────────────────────────────
check("Oct 2026 → 2026 season",        derive_season_start_year("2026-10-08"), 2026)
check("Dec 2026 → 2026 season",        derive_season_start_year("2026-12-25"), 2026)
check("Jan 2027 → 2026 season",        derive_season_start_year("2027-01-15"), 2026)
check("Jun 2027 → 2026 season",        derive_season_start_year("2027-06-10"), 2026)
check("Sep 2026 (preseason) → 2026",   derive_season_start_year("2026-09-20"), 2026)
check("Aug 2026 (offseason) → 2025",   derive_season_start_year("2026-08-01"), 2025)

# ── season code ──────────────────────────────────────────────────────────────
check("Oct 2026 → 20262027",           derive_season_code("2026-10-08"), "20262027")
check("Mar 2027 → 20262027",           derive_season_code("2027-03-31"), "20262027")
check("Apr 2026 → 20252026",           derive_season_code("2026-04-29"), "20252026")

# ── regime detection ─────────────────────────────────────────────────────────
check("opening night → regular",       detect_regime("2026-10-08"), "regular")
check("mid-season Jan → regular",      detect_regime("2027-01-15"), "regular")
check("late Mar → regular",            detect_regime("2027-03-31"), "regular")
check("Apr 10 → regular",              detect_regime("2027-04-10"), "regular")
check("Apr 19 → regular (boundary)",   detect_regime("2027-04-19"), "regular")
check("Apr 20 → playoffs (boundary)",  detect_regime("2027-04-20"), "playoffs")
check("May → playoffs",                detect_regime("2027-05-15"), "playoffs")
check("Jun Cup final → playoffs",      detect_regime("2027-06-10"), "playoffs")
check("Jul offseason → regular",       detect_regime("2027-07-15"), "regular")
check("Sep preseason → regular",       detect_regime("2026-09-25"), "regular")
check("2026 playoffs Apr 29 → playoffs", detect_regime("2026-04-29"), "playoffs")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
