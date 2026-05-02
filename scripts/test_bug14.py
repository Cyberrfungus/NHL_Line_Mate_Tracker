#!/usr/bin/env python3
"""
test_bug14.py — Unit tests for score_results.py core logic.
Covers: delete_date_rows, already_scored, build_chain_lookup, score_cold_sticks.
Run: py scripts/test_bug14.py
"""
import csv, json, os, sys, tempfile
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

import importlib.util

def _load(name, fname):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

mod = _load("score_results", "score_results.py")

FIELDS           = mod.CSV_FIELDS
build_chain_lookup  = mod.build_chain_lookup
score_cold_sticks   = mod.score_cold_sticks
delete_date_rows_fn = mod.delete_date_rows
already_scored_fn   = mod.already_scored

PASS = FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        print(f"  ✅ {name}")
        PASS += 1
    else:
        print(f"  ❌ {name}" + (f"  ({detail})" if detail else ""))
        FAIL += 1

def make_log(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def blank_row(date="2026-04-21"):
    return {k: ("" if k != "date" else date) for k in FIELDS}

print("=== test_bug14 ===\n")

# ── T1: delete_date_rows removes only the target date ────────────────────────
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "results_log.csv"
    mod.RESULTS_LOG = p
    rows = [blank_row("2026-04-21"), blank_row("2026-04-22"), blank_row("2026-04-21")]
    make_log(rows, p)
    deleted = delete_date_rows_fn("2026-04-21")
    check("T1 delete_date_rows removes correct count", deleted == 2, f"got {deleted}")
    with open(p, newline="") as f:
        remaining = list(csv.DictReader(f))
    check("T1b only other-date rows remain", all(r["date"] == "2026-04-22" for r in remaining))

# ── T2: delete_date_rows on nonexistent date → 0 deleted, file unchanged ─────
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "results_log.csv"
    mod.RESULTS_LOG = p
    make_log([blank_row("2026-04-21")], p)
    deleted = delete_date_rows_fn("2099-01-01")
    check("T2 delete nonexistent date = 0 deleted", deleted == 0)
    with open(p, newline="") as f:
        remaining = list(csv.DictReader(f))
    check("T2b file unchanged after nonexistent delete", len(remaining) == 1)

# ── T3: already_scored returns True when date present ────────────────────────
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "results_log.csv"
    mod.RESULTS_LOG = p
    make_log([blank_row("2026-04-21")], p)
    check("T3 already_scored True when date exists",
          already_scored_fn("2026-04-21"))
    check("T3b already_scored False for absent date",
          not already_scored_fn("2099-01-01"))

# ── T4: build_chain_lookup correctly pairs scorer + assists ──────────────────
chains = {"goals": [{
    "game": "A@B", "period": 1, "time": "05:00", "strength": "ES",
    "scorer": "Alpha",
    "assist1": "Beta",
    "assist2": "Gamma",
    "chain": ["Alpha", "Beta", "Gamma"],
}]}
active, pairs = build_chain_lookup(chains)
check("T4 all three chain members in active_players",
      "Alpha" in active and "Beta" in active and "Gamma" in active)
check("T4b pair Alpha+Beta in chain_pairs",
      frozenset({"Alpha", "Beta"}) in pairs)
check("T4c pair Alpha+Gamma in chain_pairs",
      frozenset({"Alpha", "Gamma"}) in pairs)

# ── T5: score_cold_sticks — player in chain = Loss, else Win ─────────────────
verified = {"cold_sticks": [
    {"name": "Alpha", "team": "A", "tier": "A", "blanks": 5, "l5_pts": 0},
    {"name": "Delta", "team": "B", "tier": "B", "blanks": 3, "l5_pts": 1},
]}
active_players = {"Alpha": [{"game": "A@B", "period": 1, "time": "05:00",
                              "strength": "ES", "scorer": "Alpha"}]}
rows = score_cold_sticks(verified, active_players, "2026-04-21")
alpha_row = next(r for r in rows if r["player"] == "Alpha")
delta_row = next(r for r in rows if r["player"] == "Delta")
check("T5 chain member = Loss", alpha_row["result"] == "L")
check("T5b absent player = Win", delta_row["result"] == "W")

# ── T6: "unassisted" string NOT in build_chain_lookup active keys ─────────────
chains_unassisted = {"goals": [{
    "game": "A@B", "period": 2, "time": "10:00", "strength": "ES",
    "scorer": "Echo",
    "assist1": "unassisted",
    "assist2": "",
    "chain": ["Echo"],   # correct: chain should NOT include "unassisted"
}]}
active2, _ = build_chain_lookup(chains_unassisted)
check("T6 'unassisted' not in active_players", "unassisted" not in active2)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(FAIL)
