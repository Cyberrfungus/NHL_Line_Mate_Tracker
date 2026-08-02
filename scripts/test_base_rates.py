#!/usr/bin/env python3
"""
test_base_rates.py — Tests for scripts/base_rates.py

Builds synthetic lineups/chains/verified files in a temp dir and checks the
blank-rate accounting: teams that did not play are excluded, injured players
are excluded, composite role strings match verify_players, and the cold-stick
edge is measured against the matching role baseline.

Run: py scripts/test_base_rates.py
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import base_rates as mod

PASS = FAIL = 0


def check(label, actual, expected):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label} — expected {expected!r}, got {actual!r}")


LINEUPS = {
    "AAA": {
        "L1": ["Scorer One", "Blank One", "Hurt One"],
        "L2": ["Blank Two"],
        "L3": [], "L4": [],
        "PP1": ["Scorer One"],
        "PP2": ["Blank Two"],
        "injuries": [{"player": "Hurt One", "status": "ir", "note": ""}],
        "scratched": [],
    },
    "BBB": {  # not on tonight's slate — must be ignored entirely
        "L1": ["Bench Guy", "Other Bench"],
        "L2": [], "L3": [], "L4": [], "PP1": [], "PP2": [],
        "injuries": [], "scratched": [],
    },
    "CCC": {
        "L1": ["Assist Guy", "Blank Three"],
        "L2": [], "L3": [], "L4": [], "PP1": [], "PP2": [],
        "injuries": [], "scratched": ["Scratched Guy"],
    },
}

CHAINS = {
    "date": "2026-01-01",
    "games_count": 1,
    "goals_count": 1,
    "games": [{"label": "AAA@CCC", "score": "1-0", "state": "FINAL"}],
    "goals": [{
        "date": "2026-01-01", "game": "AAA@CCC", "team": "AAA",
        "period": 1, "time": "10:00", "strength": "ES",
        "scorer": "Scorer One", "assist1": "Assist Guy", "assist2": "",
        "chain": ["Scorer One", "Assist Guy"],
    }],
}

VERIFIED = {
    "date": "2026-01-01",
    "cold_sticks": [
        {"name": "Blank One",  "team": "AAA", "tier": "A",
         "blanks": 5, "l5_pts": 0, "line_role": "L1", "high_role": True},
        {"name": "Scorer One", "team": "AAA", "tier": "A",
         "blanks": 5, "l5_pts": 0, "line_role": "L1+PP1", "high_role": True},
    ],
    "hot_players": [],
    "players": {},
}


# ── helper extraction ─────────────────────────────────────────────────────────

print("── teams / points extraction ──")
check("teams_that_played parses AWY@HOM",
      mod.teams_that_played(CHAINS), {"AAA", "CCC"})
check("players_with_points collects whole chain",
      mod.players_with_points(CHAINS), {"Scorer One", "Assist Guy"})
check("injured_names picks up ir status",
      mod.injured_names(LINEUPS["AAA"]), {"Hurt One"})
check("injured_names includes scratched list",
      mod.injured_names(LINEUPS["CCC"]), {"Scratched Guy"})
check("composite_role orders ES then PP",
      mod.composite_role(["PP1", "L2"]), "L2+PP1")
check("composite_role PP-only (defenseman)",
      mod.composite_role(["PP2"]), "PP2")


# ── observations ──────────────────────────────────────────────────────────────

print("\n── per-date observations ──")
obs = list(mod.date_observations(LINEUPS, CHAINS))
names = {o["name"] for o in obs}

check("non-playing team excluded", "Bench Guy" in names, False)
check("injured player excluded", "Hurt One" in names, False)
check("5 skater-games observed", len(obs), 5)

by_name = {o["name"]: o for o in obs}
check("scorer not blanked",        by_name["Scorer One"]["blanked"],  False)
check("assister not blanked",      by_name["Assist Guy"]["blanked"],  False)
check("pointless L1 blanked",      by_name["Blank One"]["blanked"],   True)
check("pointless L2 blanked",      by_name["Blank Two"]["blanked"],   True)
check("opponent pointless blanked", by_name["Blank Three"]["blanked"], True)
check("role_key for L1+PP1",       by_name["Scorer One"]["role_key"], "L1+PP1")
check("role_key for L2+PP2",       by_name["Blank Two"]["role_key"],  "L2+PP2")


# ── rate accounting ───────────────────────────────────────────────────────────

print("\n── rate accounting ──")
r = mod.Rate()
for o in obs:
    r.add(o["blanked"])
check("overall 3 blanks of 5", (r.blank, r.total), (3, 5))
check("overall blank pct 60%", round(r.pct, 1), 60.0)

empty = mod.Rate()
check("empty Rate pct is 0", empty.pct, 0.0)
check("empty Rate stderr is 0", empty.stderr, 0.0)

by_role = {}
for o in obs:
    by_role.setdefault(o["role_key"], mod.Rate()).add(o["blanked"])
check("L1 baseline 2 of 3 blank",
      (by_role["L1"].blank, by_role["L1"].total), (2, 3))
check("L1+PP1 baseline 0 of 1 blank",
      (by_role["L1+PP1"].blank, by_role["L1+PP1"].total), (0, 1))


# ── cold stick edge vs baseline ───────────────────────────────────────────────

print("\n── cold stick edge ──")
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    (d / "lineups_2026-01-01.json").write_text(json.dumps(LINEUPS), encoding="utf-8")
    (d / "chains_2026-01-01.json").write_text(json.dumps(CHAINS), encoding="utf-8")
    (d / "verified_2026-01-01.json").write_text(json.dumps(VERIFIED), encoding="utf-8")
    mod.DATA_DIR = d

    check("find_dates pairs lineups+chains",
          mod.find_dates(), ["2026-01-01"])
    check("find_dates --since filters out earlier",
          mod.find_dates(since="2026-06-01"), [])

    overall = mod.Rate()
    for o in obs:
        overall.add(o["blanked"])
    hits, expect, missing = mod.cold_stick_edge(["2026-01-01"], by_role, overall)

    # Blank One recorded no point (win); Scorer One scored (loss) → 1 of 2
    check("tier A scored 1 win of 2", tuple(hits["A"]), (1, 2))
    # Both roles have <10 baseline obs, so both fall back to the overall rate
    check("thin role buckets fall back", missing, 2)
    check("fallback baseline is overall rate",
          [round(x, 1) for x in expect["A"]], [60.0, 60.0])

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
