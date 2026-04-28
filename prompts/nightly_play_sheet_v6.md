# NHL LINEMATE DUO TRACKER — NIGHTLY PLAY SHEET v6
# ✅ Fresh Hockey-Reference playoff data used
# Upload this prompt along with tonight's data files to your Claude Project.
# Files required: lineups_DATE.json, verified_DATE.json
# Optional (recommended): goalies_DATE.json, advanced_metrics_DATE.json
#
# REGIME: 2026 PLAYOFFS — regime-separated rules in effect (STATE.md SYSTEM STATUS)
#   Tier A Cold Sticks  → LIVE BETS        (80.6% / 31 obs, ACTIVE)
#   All duo plays       → PAPER TRACK ONLY (25.6% / 39 obs, PAUSED)
#   F10 / Totals / SGPs → TRACKING ONLY    (insufficient playoff sample)
#
# CHANGELOG vs v5:
# - Section 1: Tier A Cold Sticks = only live-bet section
# - Section 2: Duos demoted to PAPER TRACK ONLY for playoff regime
# - Sections 3-6: collapsed to TRACKING ONLY
# - BET LOG REMINDER added before self-check

---

You are building tonight's verified play sheet. Complete ALL steps in order. No skipping, no skimming.

## MANDATORY PRE-FLIGHT (complete before any output)

1. Open `lineups_DATE.json` with the view tool. Print a clean team table: L1/L2/L3/L4, D1/D2/D3, PP1, PP2.
2. Open `verified_DATE.json` with the view tool. Note `data_source` field — confirm it reads `hockey-reference` for HR-sourced players. Extract hot_players and cold_sticks lists.
3. If goalies + advanced_metrics files are uploaded: open both. Build goalie tier table (blended_sv + GSAx → tier → signal).
4. Self-check: "Did I open every JSON with the view tool?" → If No, restart.

**HALT TRIGGERS (do not proceed):**
- Any player on a team they don't belong to
- Star player on L4 or 4th-liner on L1+PP1 without explanation
- Any roster anomaly that cannot be confirmed from the file itself

---

## SECTION 1 — TIER A COLD STICKS ✅ LIVE BETS

**ONLY live-bet section this sheet. Tier A cold sticks: 80.6% / 31 obs (playoff sample). ACTIVE.**

### Prop: u0.5 Points. Do NOT recommend u0.5 Goals — major books don't post it.

Data source: `verified_DATE.json` → `cold_sticks` array (L5 and blanks from HR playoff stats).

For each Tier A cold stick player, output one row:

| Player | Team | Role | Blanks | Playoff Pts | Opp Goalie Tier | PLAY? |
|--------|------|------|--------|-------------|-----------------|-------|
| [Name] | [TM] | L#/PP# | [#] | [#] | ELITE/STRONG/AVG/WEAK | ✅/⚠️/❌ |

**PLAY? logic:**
- ✅ LOCK = Tier A (5+ blanks, 0 playoff pts) + L3/L4 role + no anomalies
- ⚠️ LEAN = Tier A but on L1/L2 or PP1 (higher assist-traffic break risk)
- ❌ SKIP = Tier B only, or playoff pts > 0

**Key rules:**
- High-role cold (L1/L2 or PP1) = LEAN not LOCK.
- Cold stick + facing ELITE goalie = stronger lock.
- Cold stick + facing WEAK goalie = still valid, note elevated break risk.

**Tier B cold sticks:** List below the Tier A table. Paper track only — 70% WR not sufficient for live bets at current sample size.

---

## SECTION 2 — DUOS 📋 PAPER TRACK ONLY

**PLAYOFF REGIME: duo live betting PAUSED. Record: 25.6% / 39 obs. Do not bet these.**
**Log every duo for re-validation. Need 20+ more playoff observations before reconsidering.**

### ELITE+PP2 pairs (both share ES line + PP unit):

| Duo | Team | Shared Unit | Playoff Pts (P1+P2) | Goalie Opp | Paper Signal |
|-----|------|-------------|----------------------|------------|--------------|
| A + B | [TM] | L1+PP1 | X+Y | WEAK/AVG/STRONG/ELITE | TRACK / SKIP |

### All other duos (ELITE, PP LINK, STRONG):

List in the same format. All are paper-track only regardless of composite score.

**Hard rule:** Do not build SGPs or live bets using duo legs this sheet.

---

## SECTIONS 3-6 — 📊 TRACKING ONLY (no live bets)

**These signals have insufficient playoff sample for live deployment. Log observations only.**

### Team Totals

| Game | O/U Line | Lean | Key Drivers |
|------|----------|------|-------------|
| TM1 @ TM2 | X.5 | OVER/UNDER/NEUTRAL | [goalie tier, xGF%, pace_gf60] |

Default playoff lean: UNDER unless ≥2 of (weak goalie, xGF% >54%, pace_gf60 >3.5).

### F10 GIFT (0.5 goals, first 10 min)

| Game | Lean | Drivers |
|------|------|---------|
| TM1 @ TM2 | OVER/UNDER | [pace_gf60, goalie tier] |

Recommend F10 OVER only when: pace_gf60 >3.5 AND opposing goalie AVG or below.

### Goalie Saves, SGPs

Log any notable signals. Do not build live bets around these in playoff regime.

---

## BET LOG REMINDER

Before placing any live bet from Section 1:
- Confirm u0.5 pts line is posted at your book (bet365 / DK / FanDuel / BetMGM)
- Check player is not in injury report since verified JSON was generated
- Log immediately in `data/bet_log.csv`:
  `date, bet_description, signal_tier, stake_units, price_taken, book, closing_line, clv_cents, result, pnl_units`

---

## SELF-CHECK (mandatory before shipping)

Answer all four explicitly:

1. Did I open every JSON with the view tool this session? (Y/N)
2. Is verified JSON data source `hockey-reference` (not stale regular-season)? (Y/N)
3. Are all duo plays in Section 2 marked PAPER TRACK ONLY with no live-bet recommendation? (Y/N)
4. Are goalie tiers based on blended_sv (not raw season SV%, not role labels)? (Y/N)

**If any answer is N — rebuild that section before shipping.**

---

## PROP QUICK REFERENCE

| Prop | Regime | Signal | Books | Action |
|------|--------|--------|-------|--------|
| u0.5 Points (cold stick, Tier A) | PLAYOFFS | 80.6% / 31 obs | bet365, DK, FanDuel, BetMGM | ✅ LIVE BET |
| u0.5 Goals (cold stick) | ANY | ~92% est. | ⚠️ UNAVAILABLE at major books | N/A |
| ELITE+PP2 duo o0.5 pts | PLAYOFFS | 25.6% chain rate | DK SGP | 📋 PAPER ONLY |
| Any other duo | PLAYOFFS | 25.6% chain rate | — | 📋 PAPER ONLY |
| Team Total / F10 / SGP | PLAYOFFS | Insufficient sample | — | 📊 TRACKING |
