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
    by_es, by_pp = {}, {}
    for o in obs:
        overall.add(o["blanked"])
        if o["es_line"]:
            by_es.setdefault(o["es_line"], mod.Rate()).add(o["blanked"])
        key = o["on_pp"] or "no PP"
        by_pp.setdefault(key, mod.Rate()).add(o["blanked"])
    by_es = mod.defaultdict(mod.Rate, by_es)
    by_pp = mod.defaultdict(mod.Rate, by_pp)

    cs_picks, sources = mod.cold_stick_edge(
        ["2026-01-01"], by_role, by_es, by_pp, overall)

    # Blank One recorded no point (win); Scorer One scored (loss) → 1 of 2
    wins, total, obs, base, edge, se = mod.summarize(cs_picks)
    check("2 picks scored", total, 2)
    check("1 win of 2", wins, 1)
    # Every bucket here is under both thresholds, so all fall to all-slots
    check("thin buckets fall to all slots", sources["all slots"], 2)
    check("fallback baseline is overall rate", round(base, 1), 60.0)
    check("pick roles captured",
          sorted(p["role"] for p in cs_picks), ["L1", "L1+PP1"])
    check("both picks are HIGH role class",
          {p["role_class"] for p in cs_picks}, {"HIGH"})


# ── role class + odds helpers ─────────────────────────────────────────────────

print("\n── role class / odds helpers ──")
check("L1 is HIGH",            mod.role_class("L1"),        "HIGH")
check("L2+PP2 is HIGH",        mod.role_class("L2+PP2"),    "HIGH")
check("PP1 alone is HIGH",     mod.role_class("PP1"),       "HIGH")
check("L4 is DEPTH",           mod.role_class("L4"),        "DEPTH")
check("L3+PP2 is DEPTH",       mod.role_class("L3+PP2"),    "DEPTH")
check("PP2 alone is DEPTH",    mod.role_class("PP2"),       "DEPTH")
check("empty role is DEPTH",   mod.role_class(""),          "DEPTH")

check("80% implies -400",      mod.implied_american(80.0),  "-400")
check("50% implies -100",      mod.implied_american(50.0),  "-100")
check("40% implies +150",      mod.implied_american(40.0),  "+150")
check("degenerate 0% guarded", mod.implied_american(0.0),   "—")
check("degenerate 100% guarded", mod.implied_american(100.0), "—")

print("\n── verdict gating ──")
check("thin sample suppressed",
      mod.verdict_for(edge=30.0, se=0.0, total=2), "thin sample (n<30)")
check("large edge over 2 SE is REAL",
      mod.verdict_for(edge=10.0, se=3.0, total=100), "REAL (>2 SE)")
check("edge between 1 and 2 SE is weak",
      mod.verdict_for(edge=4.0, se=3.0, total=100), "weak (1-2 SE)")
check("edge under 1 SE is noise",
      mod.verdict_for(edge=1.0, se=3.0, total=100), "noise (<1 SE)")
check("negative edge is NO EDGE",
      mod.verdict_for(edge=-2.0, se=3.0, total=100), "NO EDGE")

check("summarize on empty group is safe", mod.summarize([]), (0, 0, 0.0, 0.0, 0.0, 0.0))


# ── baseline fallback chain ───────────────────────────────────────────────────

print("\n── baseline fallback chain ──")
big_role = mod.defaultdict(mod.Rate)
big_es   = mod.defaultdict(mod.Rate)
big_pp   = mod.defaultdict(mod.Rate)
ov       = mod.Rate()
for _ in range(50):
    big_role["L3+PP2"].add(True)      # 50 obs, 100% blank
for i in range(100):
    big_es["L3"].add(i < 70)          # 100 obs, 70% blank
for i in range(100):
    big_pp["PP2"].add(i < 60)         # 100 obs, 60% blank
for i in range(100):
    ov.add(i < 65)                    # 100 obs, 65% blank

src = mod.defaultdict(int)
check("exact composite role preferred",
      round(mod.role_baseline("L3+PP2", big_role, big_es, big_pp, ov, src), 1), 100.0)
check("falls to ES line when composite thin",
      round(mod.role_baseline("L3+PP1", big_role, big_es, big_pp, ov, src), 1), 70.0)
check("falls to PP unit when no ES line",
      round(mod.role_baseline("PP2", big_role, big_es, big_pp, ov, src), 1), 60.0)
check("falls to all slots when nothing matches",
      round(mod.role_baseline("L9+PP9", big_role, big_es, big_pp, ov, src), 1), 65.0)
check("granularity counters tracked",
      dict(src), {"exact role": 1, "ES line": 1, "PP unit": 1, "all slots": 1})

check("roles_from_lineups derives composite role",
      mod.roles_from_lineups(LINEUPS)["Blank Two"], "L2+PP2")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
