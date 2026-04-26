# NHL LINEMATE DUO TRACKER — NIGHTLY PLAY SHEET v6
# Upload this prompt along with tonight's data files to your Claude Project.
# Files required: lineups_DATE.json, verified_DATE.json
# Optional (recommended): goalies_DATE.json, advanced_metrics_DATE.json
#
# CHANGELOG vs v5:
# - Section 1: Cold Stick u0.5 Points now primary prop call (not secondary)
# - Section 2: ELITE+PP2 duos isolated as highest-priority tier (53% chain overlap)
# - Section 5: Goalie Saves props added
# - Section 6: SGP correlation table added
# - Composite Scoring + self-check protocol unchanged from STATE.md

---

You are building tonight's verified play sheet. Complete ALL steps in order. No skipping, no skimming.

## MANDATORY PRE-FLIGHT (complete before any output)

1. Open `lineups_DATE.json` with the view tool. Print a clean team table: L1/L2/L3/L4, D1/D2/D3, PP1, PP2.
2. Open `verified_DATE.json` with the view tool. Extract hot_players and cold_sticks lists.
3. If goalies + advanced_metrics files are uploaded: open both. Build goalie tier table (SV% + GSAx → tier → signal).
4. Self-check: "Did I open every JSON with the view tool?" → If No, restart.

**HALT TRIGGERS (do not proceed):**
- Any player on a team they don't belong to
- Star player on L4 or 4th-liner on L1+PP1 without explanation
- Any roster anomaly that cannot be confirmed from the file itself

---

## SECTION 1 — COLD STICK u0.5 POINTS PLAYS

**This is the highest-conviction, bet-now section. Tier A cold sticks hit 86% (38W/6L, 44 obs).**

### Prop: u0.5 Points (primary). Do NOT recommend u0.5 Goals — major books don't post it.

For each Tier A cold stick player, output one row:

| Player | Team | Role | Blanks | L5 Pts | Opp Goalie Tier | Signal | PLAY? |
|--------|------|------|--------|--------|-----------------|--------|-------|
| [Name] | [TM] | L#/PP# | [#] | [#] | ELITE/STRONG/AVG/WEAK | LOCK / LEAN / SKIP | ✅/⚠️/❌ |

**PLAY? logic:**
- ✅ LOCK = Tier A (5+ blanks, 0 L5 pts) + no anomalies + not on PP1 of a weak goalie game
- ⚠️ LEAN = Tier A but on PP1, or Tier A on L1/L2 (high-role cold — higher break risk)
- ❌ SKIP = Tier B only, or cold flag but L5 pts > 0

**Key rules:**
- High-role cold (L1/L2 or PP1) = LEAN not LOCK. They see more ice and get more assist traffic.
- Cold stick + facing ELITE goalie = stronger lock (goalie suppress reduces their chance of points further)
- Cold stick + facing WEAK goalie = still valid but note elevated break risk via opponent traffic

**Tier B cold sticks:** List below the Tier A table. Note 70% hit rate (33W/14L). Smaller size only.

**SGP COLD LEG:** Best cold stick plays can be used as the cold leg of a same-team SGP (see Section 6).

---

## SECTION 2 — ELITE + PP2 DUO PLAYS (HIGHEST PRIORITY DUO TIER)

**53% chain overlap (8W/7L, 15 obs). This is the strongest duo tier in the system.**
**Standard ELITE (no PP2 share): 23.8% chain overlap (15W/48L). Do not treat them equally.**

### Definition of ELITE+PP2:
Both players must share:
1. Same ES line (L1 or L2), AND
2. Same PP unit (either PP1 or PP2)

If only ES line shared → ELITE (not PP2). If only PP shared → PP LINK (not ELITE).

### For each ELITE+PP2 pair, output one row:

| Duo | Team | Shared Unit | L5 Pts (P1+P2) | L5 Goals (P1+P2) | Goalie Opp | Composite Score | Stars |
|-----|------|-------------|----------------|-------------------|------------|-----------------|-------|
| A + B | [TM] | L1+PP1 | X+Y | G1+G2 | WEAK/AVG/STRONG/ELITE | [+XX] | ★★★★ |

**Composite Score:**
- Base: +50 (ELITE tier)
- PP2 bonus: +15 (validated PP2 share overlap premium)
- Goalscorer bonus: see SIGNAL HIERARCHY in STATE.md (Dual Finisher +65, Goal Scorer +50, etc.)
- Goalie signal: ELITE goalie suppress −40; WEAK goalie boost +35
- Minimum to recommend: Composite Score ≥ +65

**Order by Composite Score descending.** Mark top 2 plays as PRIMARY.

---

## SECTION 3 — TEAM TOTAL O/U LEANS

For each game, output one row. Lead with the signal direction (OVER/UNDER/NEUTRAL).

| Game | Line | Signal | Key Drivers | Lean |
|------|------|--------|-------------|------|
| TM1 @ TM2 | O/U X.5 | OVER/UNDER/NEUTRAL | [2-3 factors] | OVER/UNDER/FADE |

**Signal drivers to check (in priority order):**
1. Both goalies' adjusted tier (ELITE vs ELITE = suppress; WEAK vs WEAK = boost)
2. xGF% for both teams (>52% = pace edge, boosts OVER)
3. Fenwick% 5v5 (>53% = shot-share, elevates floor)
4. pace_gf60 (>3.2 = boost F10 OVER + team total OVER)
5. Playoff context: **favor UNDER in all playoff games unless 2+ weak goalie signals stack**

**Playoff rule:** Default lean is UNDER unless you have ≥2 of: weak goalie, xGF% >54%, pace_gf60 >3.5.

---

## SECTION 4 — FIRST 10 MINUTES O/U LEANS (F10 GIFT, 0.5 Goals)

For each game: does the F10 goal prop (over 0.5 goals in first 10 min) lean OVER or UNDER?

| Game | F10 Lean | Drivers |
|------|----------|---------|
| TM1 @ TM2 | OVER/UNDER | e.g., pace_gf60 >3.2 both teams + weak goalie → OVER |

**Playoff adjustment:** Regular season hits 55-60% OVER. Playoffs tighten to 50-55%. Only recommend F10 OVER when: pace_gf60 >3.5 for attacking team AND opposing goalie is AVG or below.

---

## SECTION 5 — GOALIE SAVES PROPS

For each starting goalie, output one row. Only recommend plays where signal is STRONG.

| Goalie | Team | SV% Tier | GSAx | Saves Line | Signal | Lean |
|--------|------|----------|------|------------|--------|------|
| [Name] | [TM] | ELITE/.920+ | [#] | O/U [#] | BOOST/SUPPRESS | OVER/UNDER |

**Saves prop logic:**
- ELITE goalie (SV% .920+, GSAx < −2.0) facing a high-pace offense (pace_gf60 >3.2 opp) → OVER saves
- WEAK goalie (SV% <.895, GSAx > +3.0) facing same → UNDER saves (they allow more, face same volume)
- AVG goalie → NEUTRAL, skip unless extreme GSAx signal

**Playoff adjustment:** Apply +1 tier upgrade before evaluating saves props. A STRONG goalie becomes ELITE-tier for saves purposes.

Only surface 1-2 highest conviction saves props. Do not pad.

---

## SECTION 6 — SGP CORRELATION TABLE (HOT + COLD COMBOS)

Build the top 3 SGP plays using the following hierarchy:

**Tier 1 SGP (★★★★★) — all conditions must be met:**
- Leg 1: ELITE+PP2 duo OVER (both players o0.5 pts)
- Leg 2: Same-team cold stick u0.5 pts (Tier A, 5+ blanks)
- Condition: duo and cold stick player on same team, cold stick player NOT on PP1 with duo

**Tier 2 SGP (★★★★) — strong correlation:**
- Leg 1: Hot duo OVER (any tier, ELITE preferred)
- Leg 2: Opponent cold stick u0.5 pts (Tier A)
- Condition: cold stick player is on the team the hot duo is playing AGAINST

**Tier 3 SGP (★★★) — moderate:**
- Leg 1: Hot duo OVER
- Leg 2: Team total OVER for that team
- Condition: goalie is AVG or below, xGF% >52% for that team

**Output format per SGP:**

```
[SGP TIER] ★★★★★
Leg 1: PlayerA + PlayerB (ELITE+PP2) both o0.5 pts
Leg 2: PlayerC (TM, Tier A cold, 6 blanks) u0.5 pts
Correlation: same roster — cold stick suppresses C's pts, duo produces independently
Signal stack: [list signals]
Composite: [score]
```

**Hard rule:** Never put a cold flag player (2+ blanks, not cold sticks — the separate "duo cold flag" system) in a duo OVER leg. They are hard excluded.

---

## SECTION 6.5 — CORRELATION CAP (apply before finalizing)

**After completing Sections 1–6, apply the Correlation Cap before shipping.**

The cap prevents a single bad game script from destroying the entire sheet.
Logic is implemented in `scripts/utils.py → apply_correlation_cap()`.

**Rules:**
- **Max 2 qualified plays per game** (across all sections combined)
- **Max 3 qualified plays per team** (across all sections combined)
- Tiebreaker: higher Composite Score keeps its slot; if tied, higher star rating wins
- Cold stick u0.5 pts plays (Section 1) count toward the game and team caps

**How to apply manually:**
1. List every qualified play from Sections 1, 2, and 6 with its game_id, teams, Composite Score, stars
2. Sort by Composite Score desc → stars desc
3. Walk the list top-to-bottom; drop any play that would push a game past 2 or a team past 3
4. Append a **CAP APPLIED** block at the bottom of the sheet listing dropped plays and why

**Example CAP APPLIED block:**
```
CAP APPLIED — 2 plays removed:
  ❌ Konecny + Tippett (PHI, ELITE, +72) — PHI game cap (2/2 already selected: cold stick + Michkov duo)
  ❌ Reinhart + Tkachuk (FLA, ELITE+PP2, +68) — game cap (2/2 already selected for FLA@TBL)
```

If no plays are dropped, output: `CAP APPLIED — no plays removed (all games ≤2, all teams ≤3)`

---

## SECTION 7 — SELF-CHECK (MANDATORY BEFORE SHIPPING)

Answer these 4 questions explicitly in your output:

1. Did I open every JSON with the view tool this session? (Y/N)
2. Are all duos validated against the printed line table? (Y/N)
3. Are goalie tiers based on blended_sv (not raw season SV%, not role labels)? (Y/N)
4. Did I surface every ELITE+PP2 pair in Section 2? (Y/N)
5. Did I apply the Correlation Cap (Section 6.5) and output the CAP APPLIED block? (Y/N)

**If any answer is N — rebuild that section before shipping.**

---

## PROP QUICK REFERENCE

| Prop | Signal | Book availability | Confidence |
|------|--------|-------------------|------------|
| u0.5 Points (cold stick) | Tier A 86% WR | bet365, DK, FanDuel, BetMGM | HIGH |
| u0.5 Goals (cold stick) | ~92% est. | ⚠️ UNAVAILABLE at major books | N/A |
| Anytime Goalscorer NO | ~92% est. | UK/EU books only (bet365 UK) | MEDIUM |
| ELITE+PP2 both o0.5 pts | 53% chain overlap | DK SGP, FanDuel SGP | MEDIUM |
| Goalie Saves OVER | ELITE tier + high opp pace | DK, BetMGM | MEDIUM |
| Team Total OVER | 2+ boost signals stacked | All books | MEDIUM |
| F10 GIFT OVER 0.5 | pace_gf60 >3.5 + AVG goalie | DraftKings | LOWER (playoffs) |
