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

## 1. PRODUCT — FROZEN DEFINITIONS

A React dashboard surfacing **correlated duo targets** — two skaters likely to
combine for points in one game — for a single slate.

**These four definitions are frozen. Nothing may silently redefine them.**

| Term | Frozen definition |
|---|---|
| **W** | Both skaters recorded **≥1 point** in the game — scorer, A1, or A2, on **any** chain |
| **CW** | Those two skaters are **scorer + A1 on the same goal**. A2 does **not** count |
| **L** | Not W |
| **`rec`** | A **handwritten flag as stored on `DUOS`**. It is data, not a computed result |
| **`rec_rules`** | **Not computed yet.** The four written rules have no implementation anywhere in this lineage |

CW is a strict subset of W. Displayed as `Chain OV = CW/W` (JSX L920).

Two consequences of the frozen CW definition, both load-bearing:
- A pair that goes A1 + A2 on the same goal is **W but not CW** (e.g. `sj3`
  Orlov + W.Smith on Apr 1).
- Chains data cannot distinguish *dressed and blanked* from *did not dress*.
  A duo scored `L` may contain a scratch. Only `invalid` records that, and it
  is hand-set.

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

## 3a. FIELDS `DUOS` IS MISSING TO COMPUTE THE 4 RULES

| Rule | Needs | Present? |
|---|---|---|
| 1 — tier is ELITE or PP LINK | `tier` | ✅ stored — but hand-assigned; **verifying** it needs per-player ES/PP |
| 2 — neither blanked last 2 games | per-player blank streak | ❌ **absent** |
| 3 — chain overlap / D-QB validated last 3 slates | per-duo chain history | ❌ **absent** |
| 4 — corr is Strongest or High | `corr` | ✅ stored — same caveat as rule 1 |

Rules 1 and 4 are *checkable against stored values* but not *derivable* — the
schema has no per-player line data, so a wrong `tier` or `corr` cannot be
caught. Rules 2 and 3 cannot be evaluated at all.

**Fields that would have to exist (naming only — not implemented):**

| Field | Type | Unblocks |
|---|---|---|
| `date` | `"YYYY-MM-DD"` | everything — **`DUOS` carries no slate date at all**; the block is implicitly "today", so it cannot be joined to chain history |
| `a_es`, `b_es` | `"L1"…"L4"` \| null | derive + verify tier and corr |
| `a_pp`, `b_pp` | `"PP1"` \| `"PP2"` \| null | derive + verify tier and corr; separate dashboard-ELITE from any-shared-ES+PP1 |
| `a_blanks`, `b_blanks` | int | rule 2 (and makes `cold` derivable) |
| `chain_last3` | int | rule 3 — count of shared scorer+A1 goals in the last 3 slates |
| `dqb_confirmed` | bool | rule 3 — the D-QB branch |
| `a_key`, `b_key` | canonical id | joining to chains; `data/chains/` stores surnames only (`W.Smith`, `M.Pettersson`), and the Apr 1 block already contains `J.Carlson` alongside `Carlsson` |

`conn` (e.g. `"ES L1 + PP1"`, `"PP1 D-QB"`) encodes ES/PP informally but is a
free-text display label — 7 distinct values across 35 duos — not a parseable
substitute for structured fields.

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

## 6a. MEASURED FROM `data/chains/` — Apr 1 2026 ONLY

**Reconstructible sample: 1 slate, 35 duos, 24 goal rows.** The chain backfill
covers 16 dates (Mar 22 – Apr 6), but `DUOS` exists for **one** of them — the
Apr 1 block in the JSX. No lineups were ever saved on this lineage, so duos
cannot be rebuilt for the other 15 dates. `goalnhl_daily.csv` (Apr 7) is
**dry-run mock data** and is excluded.

Name matching: all 37 duo-slots whose player recorded a point matched the chain
CSV **exactly**; no fuzzy or surname fallback was used, so these figures carry
no name-resolution risk. The other 33 slots are players absent from Apr 1
chains — blanked or did not dress, indistinguishable here.

| Group | n | W-rate | CW-rate |
|---|---|---|---|
| ELITE | 7 | 4/7 · 57% | 1/7 · 14% |
| STRONG | 6 | 0/6 · 0% | 0/6 · 0% |
| PP LINK | 22 | 5/22 · 22% | 3/22 · 13% |
| **ALL** | **35** | **9/35 · 25%** | **4/35 · 11%** |

**The two ELITE definitions, kept separate as required:**

| Definition | n | ids | W-rate | CW-rate |
|---|---|---|---|---|
| dashboard-ELITE (`ES L1 + PP1`) | 6 | c1 s1 l1 l5 a1 sj1 | 3/6 · 50% | 1/6 · 16% |
| any shared ES + PP1 | 6 | c1 s1 l1 l5 a1 sj1 | 3/6 · 50% | 1/6 · 16% |

**They coincide on this data**, and that is an artifact, not a finding: the Apr
1 block contains no duo sharing a *non-L1* ES line plus PP1, so there is nothing
for the wider definition to pick up. The two will diverge as soon as an
`ES L2 + PP1` duo appears. `c2` (`ES L1 + PP1/PP2`) is tier ELITE but qualifies
for **neither** definition — it shares an ES line but not a PP unit (mismatch 9).

**The 6 published `rec:true` picks went 3/6 W, 3/6 CW** — every W was also a CW:

| id | duo | tier | W | CW |
|---|---|---|---|---|
| c1 | MacKinnon + Necas | ELITE | · | · |
| c3 | Toews + MacKinnon | PP LINK | **Y** | **Y** |
| a1 | Carlsson + Kreider | ELITE | · | · |
| a3 | J.Carlson + Carlsson | PP LINK | · | · |
| sj1 | Celebrini + W.Smith | ELITE | **Y** | **Y** |
| sj2 | Orlov + Celebrini | PP LINK | **Y** | **Y** |

⚠️ **n=35 on a single slate. These are not rates.** The `SEASON` block asserts
538 duo-observations; 35 are reconstructible from data in this repo. Nothing
here validates or refutes the season totals — it only shows what the stored
duos did on the one day both a duo set and its chains survive.

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
   `rec:false`.** Rules 2/3 may justify some, but they are unverifiable (§7.3).
   **Flags left untouched.** Apr 1 outcome shown for reference only:

   | id | game | tm | duo | tier | corr | W | CW | `recR` |
   |---|---|---|---|---|---|---|---|---|
   | c2 | VAN@COL | COL | MacKinnon + Landeskog | ELITE | Strongest | **Y** | · | *(empty)* |
   | c4 | VAN@COL | COL | Toews + Necas | PP LINK | High | · | · | *(empty)* |
   | c5 | VAN@COL | COL | Burns + Landeskog | PP LINK | High | **Y** | **Y** | *(empty)* |
   | v2 | VAN@COL | VAN | Hronek + Pettersson | PP LINK | High | · | · | "VAN eliminated — rule 4 motivation concern" |
   | s5 | STL@LAK | STL | Broberg + Buchnevich | PP LINK | High | · | · | *(empty)* |
   | l1 | STL@LAK | LAK | Panarin + Kopitar | ELITE | Strongest | **Y** | · | "LAK not tracked recent slates" |
   | l2 | STL@LAK | LAK | Clarke + Kopitar | PP LINK | High | · | · | "LAK not tracked recent slates." |
   | l3 | STL@LAK | LAK | Clarke + Kempe | PP LINK | High | · | · | *(empty)* |
   | l4 | STL@LAK | LAK | Clarke + Panarin | PP LINK | High | · | · | *(empty)* |
   | l5 | STL@LAK | LAK | Kopitar + Kempe | ELITE | Strongest | **Y** | · | *(empty)* |
   | l6 | STL@LAK | LAK | Doughty + Byfield | PP LINK | High | · | · | *(empty)* |
   | a4 | ANA@SJS | ANA | J.Carlson + Terry | PP LINK | High | · | · | *(empty)* |
   | a5 | ANA@SJS | ANA | J.Carlson + Kreider | PP LINK | High | · | · | *(empty)* |
   | sj3 | ANA@SJS | SJS | Orlov + W.Smith | PP LINK | High | **Y** | · | *(empty)* |

   These 14 went **W 5/14, CW 1/14** — against **3/6 and 3/6** for the six
   published picks. On one slate that separation is well inside noise and
   settles nothing; it is recorded so the comparison exists when more slates do.
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
