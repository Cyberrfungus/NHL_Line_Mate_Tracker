#!/usr/bin/env python3
"""
test_verify_players.py — Tests for the pure scoring logic in verify_players.py

Focus: the blank-streak counter (uncapped as of Aug 2026) and the cold-stick
tier rules that consume it. Network-dependent paths are not covered here.

Run: py scripts/test_verify_players.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_players import (
    count_blank_streak,
    cold_sticks_tier,
    parse_toi_minutes,
)

PASS = FAIL = 0


def check(label, actual, expected):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label} — expected {expected!r}, got {actual!r}")


def log(*points):
    """Build a most-recent-first game log from a sequence of point totals."""
    return [{"points": p} for p in points]


# ── blank streak counting ─────────────────────────────────────────────────────

print("── blank streak (uncapped) ──")
check("point in most recent game = 0 streak",
      count_blank_streak(log(1, 0, 0, 0)), 0)
check("three blanks then a point",
      count_blank_streak(log(0, 0, 0, 2, 0)), 3)
check("exactly five blanks",
      count_blank_streak(log(0, 0, 0, 0, 0, 1)), 5)

# The whole point of the change: streaks beyond 5 are no longer truncated.
check("twelve blanks is NOT capped at 5",
      count_blank_streak(log(*([0] * 12), 1)), 12)
check("twenty blanks counted in full",
      count_blank_streak(log(*([0] * 20), 3)), 20)
check("all games blank counts every game",
      count_blank_streak(log(0, 0, 0, 0, 0, 0, 0)), 7)

check("empty log is 0", count_blank_streak([]), 0)
check("missing points key treated as blank",
      count_blank_streak([{}, {}, {"points": 1}]), 2)
check("streak stops at a multi-point game",
      count_blank_streak(log(0, 0, 3, 0, 0, 0)), 2)


# ── cold stick tiers with uncapped streaks ────────────────────────────────────

print("\n── cold stick tiers ──")
check("5 blanks, 0 L5 pts = Tier A",
      cold_sticks_tier({"consecutive_blanks": 5, "last5_pts": 0}), "A")
check("12 blanks still Tier A (no crash on long streak)",
      cold_sticks_tier({"consecutive_blanks": 12, "last5_pts": 0}), "A")
check("30 blanks still Tier A",
      cold_sticks_tier({"consecutive_blanks": 30, "last5_pts": 0}), "A")
check("4 blanks, 0 pts = Tier B",
      cold_sticks_tier({"consecutive_blanks": 4, "last5_pts": 0}), "B")
check("3 blanks, 2 pts = Tier B",
      cold_sticks_tier({"consecutive_blanks": 3, "last5_pts": 2}), "B")
check("3 blanks, 3 pts = no play",
      cold_sticks_tier({"consecutive_blanks": 3, "last5_pts": 3}), None)
check("2 blanks, 5 pts = star variance, no play",
      cold_sticks_tier({"consecutive_blanks": 2, "last5_pts": 5}), None)
check("0 blanks, 0 pts = no play",
      cold_sticks_tier({"consecutive_blanks": 0, "last5_pts": 0}), None)
check("empty dict defaults to no play",
      cold_sticks_tier({}), None)

# Tier A's two conditions are equivalent by construction: a streak of 5+ means
# the L5 window is all blanks. This guards against a future edit desyncing them.
for streak in (5, 8, 15):
    check(f"streak {streak} + 0 pts is consistent Tier A",
          cold_sticks_tier({"consecutive_blanks": streak, "last5_pts": 0}), "A")


# ── TOI parsing ───────────────────────────────────────────────────────────────

print("\n── TOI parsing ──")
check("18:30 parses to 18.5",    round(parse_toi_minutes("18:30"), 2), 18.5)
check("00:00 parses to 0.0",     parse_toi_minutes("00:00"), 0.0)
check("garbage parses to 0.0",   parse_toi_minutes("nope"), 0.0)
check("None parses to 0.0",      parse_toi_minutes(None), 0.0)
check("empty string is 0.0",     parse_toi_minutes(""), 0.0)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
