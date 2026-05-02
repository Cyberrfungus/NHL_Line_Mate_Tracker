#!/usr/bin/env python3
"""
test_audit_bet_log.py — Unit tests for scripts/audit_bet_log.py
Run: py scripts/test_audit_bet_log.py
"""
import csv, io, sys, tempfile, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import the functions under test directly
import importlib.util

def _load():
    spec = importlib.util.spec_from_file_location(
        "audit_bet_log",
        Path(__file__).parent / "audit_bet_log.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

mod = _load()
audit_rows = mod.audit_rows
load_rows  = mod.load_rows
REQUIRED   = mod.REQUIRED_FIELDS

PASS = FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        print(f"  ✅ {name}")
        PASS += 1
    else:
        print(f"  ❌ {name}" + (f"  ({detail})" if detail else ""))
        FAIL += 1

def complete_row(date="2026-04-29"):
    return {
        "date": date, "bet_description": "Foerster u0.5 pts",
        "signal_tier": "cold_A", "stake_units": "1.0",
        "price_taken": "-115", "book": "DraftKings",
        "closing_line": "-120", "clv_cents": "5",
        "result": "W", "pnl_units": "0.87",
    }

def write_tmp(rows, fields=None):
    fields = fields or REQUIRED
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".csv",
                                    delete=False, newline="", encoding="utf-8")
    w = csv.DictWriter(tf, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow(r)
    tf.close()
    return Path(tf.name)

print("=== test_audit_bet_log ===\n")

# T1 — complete row → zero gaps
rows = [complete_row()]
gaps = audit_rows(rows)
check("T1 complete row = 0 gaps", len(gaps) == 0)

# T2 — empty result field → flagged with correct field name
r = complete_row(); r["result"] = ""
gaps = audit_rows([r])
check("T2 empty result flagged", len(gaps) == 1 and "result" in gaps[0][2])

# T3 — whitespace-only value treated as empty
r = complete_row(); r["clv_cents"] = "   "
gaps = audit_rows([r])
check("T3 whitespace-only = empty", len(gaps) == 1 and "clv_cents" in gaps[0][2])

# T4 — two fields missing in one row, both reported
r = complete_row(); r["book"] = ""; r["closing_line"] = ""
gaps = audit_rows([r])
check("T4 two missing fields both in list",
      len(gaps) == 1 and "book" in gaps[0][2] and "closing_line" in gaps[0][2])

# T5 — all-empty row → all 10 fields flagged
r = {k: "" for k in REQUIRED}
gaps = audit_rows([r])
check("T5 all-empty row flags all 10 fields",
      len(gaps) == 1 and len(gaps[0][2]) == len(REQUIRED),
      f"got {len(gaps[0][2])} missing")

# T6 — mixed rows: only incomplete row flagged; line number is correct
rows = [complete_row("2026-04-28"), {k: "" for k in REQUIRED}]
gaps = audit_rows(rows)
check("T6 only incomplete row flagged", len(gaps) == 1)
check("T6b line number = 3 (1 header + 2 data)", gaps[0][0] == 3)

# T7 — date filter via load_rows (uses temp file)
path = write_tmp([complete_row("2026-04-28"), complete_row("2026-04-29")])
try:
    filtered = load_rows(path=path, date_filter="2026-04-29")
    check("T7 date filter returns only matching date",
          len(filtered) == 1 and filtered[0]["date"] == "2026-04-29")
    none_filter = load_rows(path=path, date_filter=None)
    check("T7b no date filter returns all rows", len(none_filter) == 2)
finally:
    os.unlink(path)

# T8 — non-existent date filter → empty list (no crash)
path = write_tmp([complete_row("2026-04-28")])
try:
    filtered = load_rows(path=path, date_filter="2099-01-01")
    check("T8 nonexistent date → empty list, no crash", len(filtered) == 0)
finally:
    os.unlink(path)

# T9 — stake_units "0" is NOT empty (zero is valid)
r = complete_row(); r["stake_units"] = "0"
gaps = audit_rows([r])
check("T9 stake_units='0' not treated as empty", len(gaps) == 0)

# T10 — pnl_units negative value not treated as empty
r = complete_row(); r["pnl_units"] = "-1.0"
gaps = audit_rows([r])
check("T10 negative pnl_units not treated as empty", len(gaps) == 0)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(FAIL)
