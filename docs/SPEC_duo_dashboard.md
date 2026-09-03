# NHL Line-Mate Tracker — What This Project Actually Is

*Spec written Sept 3 2026 by reading the code, not the docs. Scope: the duo
dashboard lineage. Every claim is cited to a file and line.*

---

## ⚠️ 0. THE REPO CONTAINS TWO UNRELATED PROJECTS ON DIVERGENT HISTORIES

Everything this spec describes — the dashboard, the pre-game prompt, the box
score scraper, the chain CSVs — **is not on the current branch.** It lives on
orphaned commit `de0cc56`, which was replaced by a force-push:

```
+ de0cc56...0c810a0 claude/init-repo-setup-x14pg (forced update)
```

| Lineage | Head | Contains |
|---|---|---|
| **Duo dashboard** (this spec) | `de0cc56` — `origin/main` + `origin/archive/duo-dashboard-apr2026` | `NHLTrackerDashboard.jsx`, `scrape_box_scores.py`, `data/chains/`, `pregame_prompt_apr8_2026.md` |
| **Cold-stick pipeline** | `11d58f3` — `origin/claude/init-repo-setup-x14pg` | `verify_players.py`, `score_results.py`, `base_rates.py`, `.claude/STATE.md` |

They share no files and no data. The force-push rewrote only the
`claude/init-repo-setup-x14pg` branch; **`main` has pointed at `de0cc56`
throughout**, so the dashboard was never at risk of garbage collection. An
explicit archive branch was added Sept 3 2026 so this lineage keeps a stable
ref even if `main` later advances.

Note that `.claude/STATE.md` differs completely between the two lineages: 58
lines of repo-setup notes on the dashboard side, 723 lines of pipeline playbook
on the branch side. Same path, unrelated documents.

---

## 1. PRODUCT

A React dashboard surfacing **correlated duo targets** — two skaters likely to
combine for points in one game — for a single slate.

Two distinct outcomes are tracked per duo:

| Outcome | Definition | Source |
|---|---|---|
| **W** | Both players recorded a point (anywhere in the game) | prompt L75-76 |
| **L** | Not both | prompt L76 |
| **CW** | *Chain win* — goal + primary assist on the same chain, scorer and A1 **both in the duo** | prompt L76-77 |

CW is a strict subset of W. Displayed as `Chain OV = CW/W` (JSX L920).

---

## 2. HOW A DUO IS BUILT

From confirmed even-strength lines (L1–L4) and power-play units (PP1/PP2),
pasted from DailyFaceoff. Tier is assigned by which contexts the two players
share:

| Tier | Definition (prompt L47-49) | Correlation (prompt L52-55) |
|---|---|---|
| ELITE | same ES line **and** same PP unit | Strongest — ES L1 + PP1 |
| STRONG | same ES line, **different** PP units | Moderate — ES L1 only |
| PP LINK | PP connection only (D-QB→F, or F+F) | High — D-QB · Lowest — F+F |

Observed distribution across the 35 duos in the Apr 1 block: 7 ELITE,
6 STRONG, 22 PP LINK.

---

## 3. THE 4 RULES — AS WRITTEN vs AS IMPLEMENTED

**As written** (prompt L57-61) — `rec:true` only if **all four** pass:

1. Tier is ELITE or PP LINK (never STRONG)
2. Neither player blanked in their last 2 games
3. Chain overlap or validated D-QB confirmed in the last 3 slates
4. Correlation is Strongest or High

**As implemented** — the entire rec logic is one line (JSX L330):

```js
export const REC = DUOS.filter(d => d.rec && !d.cold && !d.invalid);
```

**`rec` is a hand-authored boolean literal on each duo object.** No rule is
computed. The code filters on a field a human or LLM already decided, then
re-applies cold/invalid. Rules 1–4 exist only as prose instructions to whoever
writes the block.

---

## 4. WHERE SEASON TOTALS LIVE

Hand-edited constant (JSX L10-14), rendered at L915-943:

```js
export const SEASON = {
  ELITE:    { W: 61,  L: 88,  CW: 30 },
  STRONG:   { W: 57,  L: 100, CW: 18 },
  "PP LINK":{ W: 90,  L: 142, CW: 42 },
};
```

Win% = `W/(W+L)`, Chain OV = `CW/W`, TOTAL row summed at render time. **No code
writes these.** The prompt (step 1, L190-193) asks the operator to score
yesterday's rec targets by hand and emit new totals.

---

## 5. AUTOMATED vs HAND-PASTED

**Automated — one script, and nothing consumes its output:**
- `scrape_box_scores.py` scrapes plaintextsports.com and appends to
  `data/chains/goalnhl_daily.csv` (schema: `date,game,team,scorer,assist_1,
  assist_2,type,period_time,notes`). Has `--dry-run`, `--print-only`.
- **No code anywhere reads the chain CSVs.** Grep across the whole tree at
  `de0cc56` returns only the writer. Scoring is done by eye.

**Hand-pasted into the DAILY DATA block (JSX L1-37):** `FETCH_TIME`, `SEASON`,
`GAME_ORDER`, `GAME_INFO`, and all 35 `DUOS` objects — including every
`rec`, `recR`, `cold`, `invalid`, and `top` value.

**Hardcoded in JSX body, outside DAILY DATA** (so the prompt cannot update
them): the Pre-Puck-Drop rows and the Cold Flags table (e.g. L953).

---

## 6. STALENESS (as of Sept 3 2026)

| Artifact | Last data | Age |
|---|---|---|
| Dashboard `DUOS` / `GAME_ORDER` | **Apr 1 2026** slate (VAN@COL, STL@LAK, ANA@SJS) | ~5 months |
| `SEASON` totals | thru Mar 31 2026 | ~5 months |
| `FETCH_TIME` | `"12:47 ET"` — no date | — |
| Chain backfill CSV | Mar 22 – **Apr 6 2026** (446 rows) | ~5 months |
| `goalnhl_daily.csv` | **Apr 7 2026** only (42 rows, **dry-run mock data**) | ~5 months |
| Pre-game prompt | Built for **Apr 8 2026**, never filled — still has `[PASTE …]` placeholders at L131, L140 | never run |

The scraper has never successfully run against live data in this repo.

---

## 7. MISMATCHES — PROMPT RULES vs DASHBOARD CODE

**Structural**

1. **No rule is enforced in code.** `rec` is a literal (§3). All four rules are
   applied by human judgment; the code trusts the result.
2. **Rule 1 is unenforceable.** Nothing rejects a `STRONG` duo with `rec:true`
   — it would pass the `REC` filter unchallenged.
3. **Rules 2 and 3 are not representable.** The DUOS schema (prompt L24-39) has
   no field for blank count or chain history, so those rules cannot be
   recomputed, audited, or even displayed. They are unfalsifiable after the fact.
4. **Rule 2 is redundant with the cold flag.** "Neither blanked in their last 2"
   (L59) and "blanked in 2+ consecutive games" (L63) describe the same
   condition; cold already forces `rec:false`.
5. **Cold/invalid are double-applied.** The prompt says cold and invalid force
   `rec:false` (L63-68), then L330 filters `!cold && !invalid` again. Harmless,
   but it means the code's filter is the only real guard while looking like a
   redundant one.

**Data contract violations in the Apr 1 block**

6. **14 of 35 duos pass rules 1+4 and are neither cold nor invalid, yet are
   `rec:false`** — `c2 c4 c5 v2 s5 l1 l2 l3 l4 l5 l6 a4 a5 sj3`. Rules 2/3 may
   justify some, but they are unverifiable (§7.3).
7. **11 of those 14 have an empty `recR`** — `c2 c4 c5 s5 l3 l4 l5 l6 a4 a5 sj3`.
   The schema requires `recR` to state "why it was blocked" (prompt L37). No
   reason was recorded.
8. **`v2` cites the wrong rule.** Its `recR` reads *"VAN eliminated — rule 4
   motivation concern"*, but rule 4 is correlation, and `v2` has `corr:"High"`
   which **passes**. Team motivation is not one of the four rules — this is an
   undocumented override.
9. **`c2` is mis-tiered.** `tier:"ELITE"` with `conn:"ES L1 + PP1/PP2"`. ELITE
   requires the same PP unit (L47); different units is STRONG by the written
   definition. Its own `note` concedes: *"different PP units. ELITE by ES line."*
10. **`top` and `rec` diverge.** `s4`, `l1`, `l2` are `top:true, rec:false` — two
    competing notions of "highlight this," neither defined against the other.

**Numeric**

11. **Season header date is wrong.** JSX L915 says "THRU MAR 31 2026"; the
    prompt (L74) says the same totals run through Apr 1.
12. **ELITE win% disagrees.** Prompt L79 states 41.0%; the code's formula on the
    same numbers gives `61/149 = 40.9%`. The other three tiers reconcile exactly.

**Cross-project collision (current branch vs this one)**

13. **The tier names collide with different meanings.** `score_results.py`
    emits `hot_duo_ELITE / STRONG / PP_LINK` — same labels, different rules.
    Pipeline ELITE = *any* shared ES line + shared PP1; dashboard ELITE = ES
    **L1** + PP1. The pipeline also has `ELITE_PP2`, which the dashboard lacks.
    Pipeline duos are drawn only from `hot_players` (5+ pts in L5); dashboard
    duos are drawn from all lines regardless of form.
14. **"W" means different things in the two systems.** `score_results.py` scores
    a duo `W` only when both players appear in the *same goal chain*, and records
    `both_active_no_chain` as an **L**. That is the dashboard's **CW**, not its
    **W**. So `results_log.csv` `hot_duo_ELITE` (27.7%) is a chain-win rate and
    is **not comparable** to dashboard `SEASON.ELITE` (41.0%), which is a
    both-points rate. Comparing them directly would understate the duo signal by
    roughly a third.

---

## 8. SUMMARY

The duo tracker is a **manual analytical product with a React front-end**, not
an automated system. One script writes a CSV nothing reads; every judgment that
determines a recommendation is made by hand and typed into a JavaScript literal.
The four Andy Frances rules are documentation, not logic — two of them cannot
even be checked against the data the schema stores.

It has been dormant since Apr 1 2026. It lives on `main` and on
`archive/duo-dashboard-apr2026`; the cold-stick pipeline on
`claude/init-repo-setup-x14pg` is a separate project that shares only this
repository.
