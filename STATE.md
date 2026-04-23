# NHL LINEMATE DUO CORRELATION TRACKER — STATE.md
# Source of Truth | Updated: April 14 2026
# Format: caveman compression for token efficiency

---

## PROJECT GOAL
Identify duo/trio combos where realized win rate > market implied probability.
Tracker = neutral data. Suggestion layer = filtered signal on top.
Never replace eye test. Model filters non-observable variables only.

---

## CURRENT SEASON STATS (through Apr 14 2026)
- ELITE:   ~174W ~237L | 42.3% | chain overlap ~40%
- STRONG:  ~120W ~221L | 35.2% | chain overlap ~24%
- PP LINK: ~184W ~222L | ~45.3%  | chain overlap ~44% (F+D pairs)
- TOTAL:   ~478W ~680L | ~41.3%  | 447+ deduplicated goal records
- CSV: NHL_Chain_Export_Mar22_Apr6_2026.csv + chains_2026-04-14.csv
- Apr 14 verified play sheet: 17W/12L = 58.6% (above 54.5% break-even)

## APRIL 14 RESULTS DETAIL
- UTA vs WPG: 4W/2L — Keller/Schmaltz ✅, Cooley/Guenther ✅, Sergachev F+D links ✅✅
- LAK @ VAN: 4W/0L — Panarin/Kopitar/Kempe CLEAN SWEEP, all 3 in same chain. Byfield+Moore ✅
- ANA @ MIN: 2W/2L — McTavish+Gauthier ✅ (chain overlap PP), Gauthier+Lacombe ✅. L1/L2 blanked
- MTL @ PHI: 0W/4L — Suzuki/Caufield/Slafkovsky ALL blanked. PHI rookies scored instead
- NJD @ BOS: 0W/2L — Hughes/Bratt blanked. BOS 4-0 shutout
- STL L1 (not on sheet): Thomas 2pts, Holloway 3pts, Snuggerud 4pts — would've been 3W/0L
- Cold flag skips: 1W/1L (Peterka+Kerfoot won, Peterka+Carcone lost) — net neutral, discipline justified

## COLD FLAG STATUS (entering Apr 15 2026)
### VERIFIED FROM NHL API (verify_players.py output)
**5-game blanks (HARD COLD — do not play):**
- Jesperi Kotkaniemi (CAR) — 5 blanks, 0pts L5
- Isac Lundestrom (CBJ) — 5 blanks, 0pts L5
- Cole Sillinger (CBJ) — 5 blanks, 0pts L5
- Conor Garland (CBJ) — 5 blanks, 0pts L5
- Ivan Provorov (CBJ) — 5 blanks, 0pts L5
- Ross Colton (COL) — 5 blanks, 0pts L5
- Drew Doughty (LAK) — 5 blanks, 0pts L5
- Bobby Brink (MIN) — 5 blanks, 0pts L5
- Alexandre Texier (MTL) — 5 blanks, 0pts L5
- Ivan Demidov (MTL) — 5 blanks, 0pts L5
- Oliver Kapanen (MTL) — 5 blanks, 0pts L5
- Zack Bolduc (MTL) — 5 blanks, 0pts L5
- Simon Nemec (NJD) — 5 blanks, 0pts L5
- Ville Koivunen (PIT) — 5 blanks, 0pts L5
- Justin Brazeau (PIT) — 5 blanks, 0pts L5
- Ben Kindel (PIT) — 5 blanks, 0pts L5
- Drew O'Connor (VAN) — 5 blanks, 0pts L5
- Elias Pettersson (VAN) — 5 blanks, 0pts L5
- Tom Willander (VAN) — 5 blanks, 0pts L5
- Nino Niederreiter (WPG) — 5 blanks, 0pts L5
- Isak Rosen (WPG) — 5 blanks, 0pts L5

**3-4 game blanks (COLD — strong suppress):**
- Denton Mateychuk (CBJ) — 3 blanks
- Yegor Sharangovich (CGY) — 3 blanks
- Valeri Nichushkin (COL) — 3 blanks
- Owen Tippett (PHI) — 3 blanks
- Avery Hayes (PIT) — 3 blanks
- Rutger McGroarty (PIT) — 3 blanks
- Michael Carcone (UTA) — 3 blanks
- JJ Peterka (UTA) — 3 blanks
- Brad Lambert (WPG) — 3 blanks
- Rasmus Ristolainen (PHI) — 4 blanks (also SCRATCHED 4/14)

**2-game blanks (WATCH — playable with strong context):**
- Nathan MacKinnon (COL) — 2 blanks but 4pts L5
- Gabriel Landeskog (COL) — 2 blanks, 1pt L5
- Brent Burns (COL) — 2 blanks, 3pts L5
- Brandt Clarke (LAK) — 2 blanks, 2pts L5
- Mikey Anderson (LAK) — 2 blanks, 2pts L5
- Logan Cooley (UTA) — 2 blanks but 5pts L5
- Nick Schmaltz (UTA) — 2 blanks but 5pts L5
- Bo Horvat (NYI) — 2 blanks
- Mathew Barzal (NYI) — 2 blanks, 3pts L5
- Josh Morrissey (WPG) — 2 blanks, 3pts L5
- Cole Perfetti (WPG) — 2 blanks
- Philip Broberg (STL) — 2 blanks

**CLEARED (previously flagged, now producing):**
- Martin Necas (COL) — CLEARED: 5pts (2G) L5, broke streak
- Chris Kreider (ANA) — CLEARED: 3pts L5 (but 0G, monitor)
- W.Smith: CLEARED Apr 6
- Clarke: CLEARED Apr 4

**Cold flag record: 0W/29L+ across 8 slates — signal confirmed**
**Apr 14 cold skip result: 1W/1L — net neutral, discipline justified**

---

## VALIDATED SIGNALS (our data only)

| Signal | Evidence | Sample | Status |
|--------|----------|--------|--------|
| Cold flag suppress | 0W/29L+ | 29+ obs | CONFIRMED |
| Elite goalie suppress | 0W/5L | 5 obs | DIRECTIONAL |
| Backup goalie boost | 10W/1L | 11 obs | DIRECTIONAL |
| ELITE vs STRONG gap | 42% vs 35% | 600+ obs | CONFIRMED |
| F+D PP LINK chain rate | 44.8% chain overlap | ~50 obs | CONFIRMED |
| Hot goalscorer filter | 17W/12L (58.6%) | 29 obs | PROMOTED — Signal #3 |
| Verified play sheet | 58.6% vs 35% unfiltered | 29 obs | ABOVE BREAK-EVEN (1 slate) |

## GOALIE OPPOSITION WIN RATES (our data)
- BACKUP:  10W/1L  = 90.9%
- AVG:     18W/21L = 46.2%
- STRONG:  1W/9L   = 10.0%
- ELITE:   0W/5L   = 0.0%
NOTE: Middle buckets need more tagged observations

## HOT GOALSCORER LAYER (validated Apr 14 — promoted to Signal #3)
**Thesis:** L5 Goals > L5 Points for duo prediction. Players scoring goals generate chains; assist accumulators feed chains but don't anchor them.

### Goal-Scorer Tiers (apply to both players in duo)
- **DUAL FINISHER**: Both players L5G ≥ 3 → highest priority, strongest chain overlap signal
- **GOAL SCORER**: Both players L5G ≥ 2 → strong play
- **FINISHER + PLAYMAKER**: One player L5G ≥ 3, partner L5G ≥ 1 → playable with ELITE tier
- **EXCLUDE**: Either FORWARD with L5G = 0 → filter out regardless of point total
- **D-MAN EXCEPTION**: Defensemen exempt from zero-goal exclusion on PP LINK F+D duos. D-man role = PP QB (assist generation), not finishing. Example: Hutson 0G/4A L5 is exactly what a PP D-man should look like. The FORWARD side of the F+D pair needs goals, not the D-man.

### Validation Data
- Apr 14: McTavish+Gauthier (both hot goalscorers) = WIN with chain overlap
- Apr 14: Panarin+Kempe (both hot, Kempe 5G L5) = WIN with chain overlap
- Apr 14: MTL L1 (Suzuki/Caufield/Slafkovsky — hot points but low goals) = ALL BLANKED
- Apr 14: verified play sheet with goal filter = 17W/12L (58.6%) vs ~35% unfiltered

### Known Forward Exclusion Examples (high P, zero G)
- Duchene (0G/6P), Point (0G/3P), Wennberg (0G/3P) — filter out
- These forwards accumulate assists but don't anchor scoring chains

### Metadata Tag Addition
GOALS field added: `DF` (dual finisher) | `GS` (goal scorer) | `FP` (finisher+playmaker) | `NG` (no goals)

---

## NIGHTLY BUILD PROTOCOL

### PRE-GAME STEPS (Terminal)
1. `py fetch_dfo.py --date YYYY-MM-DD --teams [TONIGHT'S TEAMS ONLY]`
2. `py verify_players.py --date YYYY-MM-DD --elite-only`
3. Upload lineups + verified JSONs to Claude
4. Claude: goalie check (DFO starting goalies + NHL.com previews)
5. Claude: generate verified play sheet (ELITE + F+D PP LINK, hot players, skip cold)

### PLAY SHEET FILTERS (in priority order)
1. Remove any player with 2+ consecutive blanks (COLD flag)
2. Remove any confirmed scratch/injury (NHL.com preview cross-check)
3. Remove any FORWARD with L5G = 0 (goal-scorer filter — D-men exempt on F+D plays)
4. Prioritize ELITE tier + PP LINK F+D (★★★+)
5. Rank by goal concentration: DUAL FINISHER > GOAL SCORER > FINISHER+PLAYMAKER
6. Prioritize teams with real motivation (playoff race, seeding, home ice)
7. Boost duos facing BACKUP or WEAK goalie
8. Suppress duos facing ELITE goalie

### TRACKER OUTPUT FORMAT (per game)
```
TEAM vs TEAM | O/U: X.X | Facing: [Goalie] GSAx [+/-X.XX] B2B[Y/N]

DUO PLAYS:
Player1 + Player2 | TIER | ★★★★ | Hot/Cold status | Goalie signal
```

### POST-GAME STEPS
1. `py fetch_chains.py YYYY-MM-DD`
2. Upload chain file to Claude
3. Score play sheet: W/L per duo, chain overlap Y/N
4. Update cold flags from verify data
5. Update STATE.md

---

## METADATA TAG SCHEMA
Format: [TIER]_[COLD]_[GOALIE]_[OU]_[B2B]_[TYPE]_[GOALS]

TIER:   ELITE | STRONG | PPLINK
COLD:   NC (no cold flag) | CF (cold flagged)
GOALIE: ELITE | STRONG | AVG | WEAK | BACKUP
OU:     50 | 55 | 60 | 65 | 70 (drop decimal)
B2B:    Y | N
TYPE:   DUO | TRIO
GOALS:  DF (dual finisher) | GS (goal scorer) | FP (finisher+playmaker) | NG (no goals/excluded)
Example: ELITE_NC_BACKUP_65_N_DUO_DF

---

## GOALIE TIER DEFINITIONS
| Tier | GSAx Threshold | Min GP | Notes |
|------|---------------|--------|-------|
| ELITE | > +0.40 | 40 | Suppress — 0% duo WR |
| STRONG | +0.20 to +0.40 | 40 | Caution |
| AVG | -0.20 to +0.20 | 40 | Neutral |
| WEAK | < -0.20 | 40 | Boost |
| BACKUP | Any | <25 | Boost — 91% duo WR |
Source: MoneyPuck goalie CSV, DFO Starting Goalies page

---

## TIER SYSTEM
- ELITE = ES line + PP unit shared (double exposure) — 42.3% WR
- STRONG = ES line only — 35.2% WR
- PP LINK = PP unit only, different ES lines
- PP LINK F+D ★ = elevated sub-tier, 44.8% chain overlap rate

## CORRELATION STRENGTH RATINGS
- ★★★★ = ELITE + confirmed shared PP1
- ★★★  = PP LINK F+D with validated chain overlap data
- ★★   = STRONG and PP LINK F+F
- ★    = weak or cross-line duos

---

## SIGNAL HIERARCHY (when signals conflict)
Cold Flag suppress → Elite goalie suppress → Hot goalscorer filter (D-man exempt on F+D) → Backup goalie boost → O/U boost

---

## ANDY FRANCES METHODOLOGY (reverse-engineered)
Base plays (1.00u): ES trio L1 + ES trio L2 per team
Kickers (0.50u): F o/1.5 pts + PP D assist (always D as assist only)
Odds floor: +100 | Base avg: +374 | Kicker avg: +808
Books: Bet365, Hard Rock, Fanatics, BetMGM, ScoreBet, Fanduel
Key rule: D-men appear in kickers ONLY, never base plays

---

## DATA SOURCES
- plaintextsports.com → chain data (fetch index first, then game slugs)
- DFO → line combos (Selenium scraper: fetch_dfo.py)
- DFO goalies → dailyfaceoff.com/starting-goalies
- NHL API → verify_players.py for L5 game logs + hot/cold detection
- NHL.com game previews → lineup cross-reference (catches scratches DFO misses)
- MoneyPuck → goalies CSV for GSAx

---

## SCRIPTS (in project root)
- `fetch_dfo.py` — Selenium DFO scraper (original). Args: --date, --teams
- `fetch_lineups_nhl.py` — Plain HTTP DFO scraper (replaced Selenium). Offset bug PATCHED by user 4/15.
- `verify_players.py` — NHL API L5 game logs. Args: --date, --elite-only, --team
- `fetch_chains.py` — Post-game chain fetcher (TBD)
- Operations Manual: NHL_Duo_Tracker_Operations_Manual.docx

## DFO SCRAPER BUG (discovered 4/15 — patched by user)
**Problem:** `fetch_lineups_nhl.py` was reading "Starting Goalies" and "Line Combination" as player names in slots 0-1, pushing every real player down by 2 positions.
- L1 got only 1 of 3 players (the LW from slot 2)
- L2 got L1's C + L1's RW + L2's LW — cascaded through all lines/D-pairings
- PP units less affected (separate HTML section)
- Confirmed 4/15: cross-checked VGK scraper vs NHL.com preview — every ES line was wrong

**Status:** User patched the scraper. Verify output on first playoff slate.

**Backup workaround:** NHL.com game preview pages render plain text lineups (`LW -- C -- RW`) without JS. URL: `nhl.com/news/[away]-[home]-game-preview-[month]-[day]-[year]`

## TERMINAL WORKFLOW (copy-paste ready)
```
py fetch_dfo.py --date YYYY-MM-DD --teams [TEAMS]
py verify_players.py --date YYYY-MM-DD --elite-only
```
Post-game:
```
py fetch_chains.py YYYY-MM-DD
```

---

## WHAT WE DON'T DO
- No hardcoded goalie tier lists (go stale)
- No automatic play suppression (display flags only)
- No ML models (insufficient sample size)
- No GSAx for backups (unreliable low sample)
- No parlaying across games
- Never replace eye test with model

---

## HONEST PERFORMANCE SUMMARY
Current overall win rate: ~41% (up from ~35-37%)
Break-even at -120: 54.5%
Verified play sheet (Apr 14): 58.6% (17W/12L) — ABOVE BREAK-EVEN
Best filter combo: ELITE + hot goalscorer + backup goalie + motivated team
Gap: Closing. One slate above break-even is not a trend yet.
Biggest lever confirmed: verification layer (killed ~40% bad plays on 4/14)

---

## ROADMAP (updated Apr 15)
1. ✅ Goalie name + tier in nightly build — DONE
2. ✅ Hot goalscorer verification layer — DONE (verify_players.py)
3. ✅ Operations manual — DONE
4. ✅ Goal-scorer filter promoted to Signal #3 with tier taxonomy + D-man exception — DONE
5. ✅ DFO scraper offset bug patched by user — DONE (verify on first playoff slate)
6. Build tonight.py wrapper (auto-detect playing teams, run fetch + verify)
7. Add O/U to every game header
8. Add metadata tag (with GOALS field) to every logged result
9. Real odds sourcing (confirm +EV at actual market prices)
10. CLV tracking
11. Filter-combination win rate table (needs 30+ obs per combo)
12. Playoff deployment: separate duo tracker + F10 Under React dashboards
