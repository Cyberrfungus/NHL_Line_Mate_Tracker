# NHL LINEMATE DUO CORRELATION TRACKER — STATE.md
# Source of Truth | Updated: April 22 2026 (post-Apr 21 scored, pre-Apr 22 Day 5)
# Format: caveman compression for token efficiency

---

## 🛑 MANDATORY PRE-FLIGHT PROTOCOL (READ FIRST EVERY SESSION)

**Claude MUST complete every step below BEFORE generating any duo, SGP, or tracker output. No exceptions. No shortcuts. Skimming file contents from context ≠ reading the file.**

### STEP 0 — Claim verification
- If this STATE.md says a signal exists, do NOT trust it blindly. Verify against uploaded files.
- If memory/summary says a player is on team X, do NOT trust it. Verify from lineups JSON.

### STEP 1 — Read lineups_YYYY-MM-DD.json with `view` tool
- Print a clean table per team: L1/L2/L3/L4, D1/D2/D3, PP1, PP2
- **Any roster anomaly (player on unexpected team, unusual line role) → HALT. Flag to user. Do NOT proceed until resolved.**
- Examples of anomalies that require HALT:
  - Player appears on team they don't belong to (check user memory + known trades)
  - Star player on L4, or 4th-liner on L1+PP1
  - Missing starter not listed in injuries section
- "Flag and proceed with disclaimer" is NOT acceptable. Either confirm or stop.

### STEP 2 — Read verified_YYYY-MM-DD.json with `view` tool
- Extract `hot_players` list (L5 5+ pts) into a working table with team/pts/goals
- Extract `cold_sticks` list, split Tier A / Tier B, note line role (L#+PP#)
- Flag "high-role cold" players: Tier A/B who occupy L1/L2 ES or PP1 slots

### STEP 3 — Read goalies_YYYY-MM-DD.json with `view` tool
- **TIER GOALIES BY SV% NUMBERS ONLY, NEVER BY ROLE LABEL**
- SV% tiers:
  - ELITE: .920+
  - STRONG: .905–.919
  - AVG: .895–.904
  - WEAK: <.895
- The word "backup" or "starter" is metadata, not signal. A .915 "backup" is not a fade.
- Output a goalie tier table with signal direction (BOOST / SUPPRESS / NEUTRAL) per team.

### STEP 4 — Duo generation (hot-player-first, not team-first)
- Iterate each hot player
- For each hot player, enumerate ALL valid correlations:
  - Same ES line? → STRONG (or ELITE if also PP1 together)
  - Same PP unit only? → PP LINK (F+F or F+D)
  - Neither? → NOT a duo. Do not generate.
- **Hard validation rule: Before adding any duo to the board, state out loud which shared unit justifies it (e.g., "both L2 ES + both PP1 = ELITE"). If you can't name a shared unit, the duo is invalid.**
- Re-check every duo against the Step 1 line table. If a player is listed on L1 in one duo and L3 in another, something is wrong — go back to Step 1.

### STEP 5 — Apply signal layers
- Cold flag suppress (hardest signal, 0W/38L+ history)
- Elite/Strong goalie SV% suppress
- Weak goalie SV% boost (.887, .888 territory)
- Hot goalscorer filter

### STEP 6 — SGP construction
- Same-team cold SGP: hot duo O + hard cold teammate u0.5 (highest correlation)
- Cross-team cold SGP: hot duo O + cold opponent u0.5
- Only rank SGPs ★★★★★ if ALL of: both duo players hot, shared unit confirmed, goalie signal favorable, cold leg is Tier A (not B)

### STEP 7 — Self-check before shipping artifact
Ask these four questions, answer them in output:
1. Did I open every JSON with `view` tool this session? (Y/N — if N, restart)
2. Are all duos validated against the printed line table? (Y/N)
3. Are goalie tiers based on SV% numbers, not role labels? (Y/N)
4. Did I surface every hot player in at least one duo? (Y/N)

**If any answer is N, do not ship. Rebuild.**

---

## ❌ FAILURE MODES LOGGED (Apr 22 session)

These are the specific errors that triggered this protocol. Do not repeat:

1. **Skim-read hallucination.** Claude read lineups JSON visually in context window, proceeded to build without using `view` tool. Result: contradicted own source data (Zegras L1 C vs "Zegras+Michkov duo" with Michkov on L3).

2. **Roster-anomaly laundering.** Saw "Quinn Hughes on MIN D1", flagged uncertainty, PROCEEDED ANYWAY with disclaimer. Disclaimers are not diagnostics. Either confirm or HALT.

3. **Role-label goalie tiering.** Tagged Wallstedt "AVG (BACKUP START)" and built "DAL primary deploy vs backup" thesis. Actual SV% .915 = STRONG tier. The word "backup" ate the numbers. Process: tier by SV% always, role label is secondary metadata.

4. **Hot-player underweighting.** Martone 7pts/3G on L2 RW + PP2 vs .887 goalie was the highest-signal individual on the slate. Appeared in 1 duo. Should have appeared in 4+ (Konecny+Martone, Dvorak+Martone, Martone+Zegras PP2, Martone+Cates PP2). Cause: built duos team-by-team from template memory instead of iterating hot players as seeds.

5. **Template-driven output.** Filled in the expected tracker shape (games → duos → cold → SGPs → JSX) from memory of STATE.md format, using source files as loose confirmation rather than primary input. The template is the output, not the workflow. Workflow = read files → validate → generate → self-check.

---

## PROJECT GOAL
Identify duo/trio combos where realized win rate > market implied probability.
Tracker = neutral data. Suggestion layer = filtered signal on top.
Never replace eye test. Model filters non-observable variables only.

---

## CURRENT SEASON STATS (through Apr 21 2026)
- ELITE:   ~180W ~251L | ~41.8% | chain overlap ~40%
- STRONG:  ~122W ~232L | ~34.5% | chain overlap ~24%
- PP LINK: ~188W ~232L | ~44.8% | chain overlap ~44% (F+D pairs)
- TOTAL:   ~490W ~715L | ~40.7%
- Apr 19 verified: 2W/6L = 25% ❌
- Apr 20 verified: 3W/10L = 23.1% ❌
- Apr 21 verified: 5W/13L = 27.8% ❌

**PLAYOFF DUO RECORD: ~10W/29L = 25.6% ❌ STRUCTURAL CONCERN**

## APR 21 RESULTS (post-game scored)

### DUO PRIORITY SHEET: 5W/13L (27.8%)
**Wins (5):**
- ✅ UTA Cooley+Guenther — both scored, chain overlap ES P3 14:00 (Guenther 1G+1A, Cooley 1G)
- ✅ VGK Marner+Stone — PP1 chain overlap (Stone 1G, Marner 1A, Eichel 1A)
- ✅ BOS Geekie+Pastrnak — ES chain overlap P2 16:29 (Geekie 1G, Pastrnak 2A)
- ✅ BOS Pastrnak+McAvoy (PP LINK F+D) — PP chain overlap P2 18:10 (Pastrnak 2A, McAvoy 1A on Zacha goal)
- ✅ MTL Suzuki+Hutson (PP LINK F+D) — PP chain overlap P1 16:11 despite Vasi ELITE suppress

**Losses (13):**
- LAK Byfield+Laferriere (Laferriere 0)
- COL MacKinnon+Necas (MacK 0)
- UTA Keller+Schmaltz (both 0)
- TBL Point+Kucherov (Point 0)
- BUF Norris+Doan (both 0)
- UTA Peterka+Kerfoot, UTA Kerfoot+Carcone, BUF McLeod+Quinn, COL MacKinnon+Makar, COL Necas+Makar, UTA Keller+Sergachev, UTA Crouse+Weegar, TBL Point+Raddysh

**Chain overlap rate: 5/18 = 27.8%** (all on PP1 or structured ES, zero rush)

### COLD STICKS TIER A APR 21: 16W/2L (88.9%) ✅
**Breaks:**
- ❌ BUF Malenstyn — 1A on Byram ES goal P3 13:54
- ❌ VGK Barbashev — 1G ES P2 15:58

v2 filter not needed — both breaks were real mid-game ES goals, not garbage time.

### COLD STICKS TIER B APR 21: 6W/5L (54.5%) ❌
**Breaks:**
- ❌ BOS Mittelstadt — 2A (on both Arvidsson ES goals P2+P3)
- ❌ BUF Dahlin — 1A on Krebs PP
- ❌ COL Kadri — 1A on Roy OT goal
- ❌ MTL Danault — 1A on Anderson ES

Tier B soft cold signal weaker than hard. Need filter tightening (Mittelstadt L2+PP2 is a miss pattern — soft cold on top-6 role breaks on assist traffic).

### KEY LEARNINGS APR 21
- **Tier A cold sticks = strongest signal in system.** 80.6% cumulative over 31 obs.
- **Tier B cold needs tighter filter** — break pattern is soft cold on PP unit assists.
- **Duo system 27.8% over 3 playoff slates = structural problem.** Market sharper on ELITE lines, tight defense, low totals.
- **Chain overlaps that DID hit: all 5 on PP1 or structured ES.** ZERO rush-chain overlaps. Playoff chain mix shifts toward special teams and set plays.
- **SGP Tier 1 Apr 21: 1W/6L.** Cold-teammate legs mostly held but duo legs failed. Barbashev scored (break) on one SGP.

---

## CUMULATIVE COLD STICKS (through Apr 21)
- Tier A: 25W/6L = **80.6%** ✅ ABOVE PLAN
- Tier A v2 (exclude last-4min/EN): pending Apr 21 recount (no garbage-time breaks tonight)
- Tier B: 12W/7L = **63.2%** 🟡 below plan, need filter tightening

---

## APR 22 PLAYOFF DAY 5 — SLATE (3 games)

### GAMES
- ANA @ EDM G2 (ANA leads series)
- DAL @ MIN G3
- PHI @ PIT

### GOALIE TABLE (SV%-TIERED, from goalies_2026-04-22.json)
| Team | Goalie | SV% | GAA | TIER | Signal |
|------|--------|-----|-----|------|--------|
| MIN | Wallstedt | **.915** | 2.61 | STRONG | mild suppress DAL |
| PHI | Vladar | .906 | 2.42 | STRONG | mild suppress PIT |
| DAL | Oettinger | .899 | 2.62 | AVG | neutral (NOT elite by numbers) |
| EDM | Ingram | .898 | 2.60 | AVG | neutral |
| ANA | Dostal | **.888** | 3.12 | WEAK | 🔥 BOOST EDM duos |
| PIT | Skinner | **.887** | 2.92 | WEAK | 🔥 BOOST PHI duos |

**Primary deployment lanes tonight:**
- PHI duos vs Skinner (.887) — Martone + Konecny + Dvorak + Zegras + Michkov all live
- EDM duos vs Dostal (.888) — McDavid/Hyman/Bouchard/Draisaitl live
- PIT top unit (Malkin/Karlsson/Crosby) vs Vladar neutral — internal quality carries

**KILLED signals:**
- ❌ "DAL BACKUP BOOST vs Wallstedt" — Wallstedt .915 is STRONG tier, not a fade. Reverse.
- ❌ "MIN vs Oettinger ELITE" — Oett .899 is AVG, mild suppress only.

### ANOMALY FLAGS (UNRESOLVED — HALT on deploy)
- **Quinn Hughes listed as MIN D1 in lineups JSON.** Historical roster = VAN. Not in user memory as traded. Do NOT deploy any MIN D-stack duo tonight until verified via DFO screenshot or trade news.

### COLD STICKS APR 22 (from verified_2026-04-22.json)
**Tier A (9):** Washe (ANA L4), Moore (ANA L4), Faksa (DAL L4), **Savoie (EDM L1+PP2)** ⚠, **RNH (EDM L3+PP1)** ⚠, Brink (MIN L3+PP2), Hathaway (PHI L4), Brazeau (PIT L3), Lizotte (PIT L4)

**Tier B (12):** Kapanen (EDM L2), Frederic (EDM L4), Sturm (MIN L4), **Ristolainen (PHI D1+PP1)** ⚠, Sennecke (ANA L2), Steel (DAL L3), Back (DAL L4), Roslovic (EDM L3), Ekholm (EDM D1), Faber (MIN D1+PP2), **Tippett (PHI L1+PP1)** ⚠, Glendening (PHI L4)

⚠ = high-role cold (on L1/L2 or PP1)

### HOT PLAYERS TO SEED DUO GENERATION
- **EDM:** McDavid 12/5 🔥🔥, Draisaitl 6/2, Hyman 5/2, Bouchard 7/0, Dach 3/2
- **DAL:** Robertson 7/5, Johnston 6/4, Bourque 6/4, Duchene 6/0, Hryckowian 4/2, Lindell 4/1
- **MIN:** Kaprizov 6/5, Hartman 6/3, JEE 6/1, Boldy 6/2, MoJo 4/1, Foligno 3/1, Tarasenko 3/1
- **PHI:** Michkov 8/3, **Martone 7/3** 🔥, Zegras 6/3
- **PIT:** Malkin 8/4, Crosby 7/1, Karlsson 6/2, Mantha 5/3
- **ANA:** Gauthier 6/5 🔥🔥, Granlund 6/0, Carlsson 3/2, Terry 3/1, Killorn 3/2, McTavish 5/2, Carlson 5/3, Lacombe 3/1

### SESSION NOTE
Apr 22 session included 4 corrections (Hughes anomaly, PHI line wrong, Wallstedt mistier, Martone underweight). Root cause: skim-read + template-driven build. Pre-flight protocol added to top of STATE.md to prevent recurrence.

**Next session must:** use `view` on every JSON, print line tables, tier goalies by SV% only, seed duos from hot players.

---

## VALIDATED SIGNALS
| Signal | Evidence | Sample | Status |
|--------|----------|--------|--------|
| Cold flag suppress | 0W/40L+ | 40+ obs | CONFIRMED |
| Tier A cold stick u0.5 | 25W/6L (80.6%) | 31 obs | CONFIRMED |
| Tier B cold stick u0.5 | 12W/7L (63.2%) | 19 obs | BELOW PLAN |
| Weak goalie boost (SV% <.895) | 10W/1L | 11 obs | DIRECTIONAL |
| Strong/Elite goalie suppress | directional | small sample | DIRECTIONAL |
| ELITE vs STRONG duo gap | 42% vs 35% | 650+ obs | CONFIRMED |
| F+D PP LINK chain rate | 44.8% chain overlap | ~55 obs | CONFIRMED |
| Hot goalscorer filter | tracking | 45+ obs | TRACKING |
| Playoff ELITE slump | 10W/29L last 3 slates | 39 obs | NEGATIVE — MONITOR |

---

## SIGNAL HIERARCHY
Cold Flag suppress → Goalie SV% tier (boost or suppress) → Hot goalscorer filter → O/U boost

---

## SCRIPTS (project root)
- `fetch_lineups_nhl.py` — Plain HTTP DFO scraper. Status: WATCH (2 clean slates)
- `verify_players.py` — NHL API L5 + Cold Sticks v1
- `scripts/fetch_postgame.py chains` — post-game chain fetcher

## TERMINAL WORKFLOW
Pre-game: `py fetch_lineups_nhl.py` → `py verify_players.py --date YYYY-MM-DD --elite-only`
Post-game: `py scripts/fetch_postgame.py chains`

---

## ROADMAP (updated Apr 22)
1. ✅ Goalie + tier in nightly build
2. ✅ Hot goalscorer verification layer
3. ✅ Operations manual
4. ✅ Goal-scorer filter Signal #3
5. 🟡 DFO scraper offset bug — 2 consecutive clean slates; status WATCH
6. ✅ Post-game script renamed fetch_postgame.py
7. ✅ Cold Sticks engine v1 shipped
8. ✅ Apr 21 slate scored
9. 🟡 Cold Sticks v2 (exclude last 4 min 3rd + EN/SH) — logic validated Apr 20; ship to script
10. ⏳ tonight.py wrapper
11. ⏳ O/U to every game header in script
12. ⏳ Metadata tag with GOALS field
13. ⏳ Real odds sourcing
14. ⏳ CLV tracking
15. ⏳ Filter-combo win rate table (30+ obs per combo)
16. ⏳ Cold Sticks v2: opposing goalie cross-ref + PP1 flag
17. ✅ Playoff deployment: duo tracker + SGP sheet React dashboards
18. ⏳ F10 Under project (separate system)
19. 🟡 INVESTIGATE: Playoff ELITE slump (10W/29L over 3 slates). Need 2 more slates before structural filter change.
20. 🆕 **Hot-player-first duo generator** — iterate hot players as seeds, enumerate all valid linemate correlations, then rank. Replaces template-driven team-by-team build.
21. 🆕 **Goalie tier = SV% numbers only** — never role label. Add as hard rule in script.
22. 🆕 **Roster anomaly halt protocol** — if lineup JSON contains player on unexpected team or unusual role, HALT. Do not generate with disclaimer.

---

## APR 22 SESSION LOG
- Apr 21 scored: duo 5W/13L (27.8%), Tier A cold 16W/2L (88.9%), Tier B cold 6W/5L (54.5%)
- Cumulative: Tier A 25W/6L (80.6%) ✅, Tier B 12W/7L (63.2%) 🟡
- 4 correction cycles required on Apr 22 build (Hughes, PHI lines, Wallstedt, Martone)
- Added mandatory pre-flight protocol to STATE.md top
- Added roadmap items 20/21/22 for process fixes
- Goalies tiered correctly on recount: Skinner .887 WEAK = primary PHI boost, Dostal .888 WEAK = EDM boost
- Martone (PHI L2 RW + PP2, 7pts/3G) is top individual signal; rebuilt SGP board around him
- Hughes anomaly: deploy halt on MIN D-stacks until verified
- Next session: verify Quinn Hughes roster status, score Apr 22 chains, evaluate playoff ELITE slump investigation
