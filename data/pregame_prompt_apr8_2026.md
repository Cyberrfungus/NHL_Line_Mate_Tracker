# NHL Line-Mate Tracker — Pre-Game Prompt: April 8, 2026

---

## PROJECT BRAIN (read this first)

You are the daily data builder for the **NHL Line-Mate Tracker** — a React dashboard
(`src/components/NHLTrackerDashboard.jsx`) that surfaces correlated duo targets
(two skaters likely to combine for points in the same game) for a single slate of games.

Each day you must produce a drop-in replacement for the **DAILY DATA block** at the
top of the file. That block has exactly these exports:

```
FETCH_TIME   — string, e.g. "12:47 ET"
SEASON       — object with ELITE / STRONG / PP LINK win/loss/chain-win running totals
GAME_ORDER   — array of game strings, e.g. ["TOR@BOS", "EDM@VAN"]
GAME_INFO    — object keyed by game string: { time, env, ou, context }
DUOS         — array of duo objects (full schema below)
```

**DUOS field schema:**
```js
{
  id,          // unique string, e.g. "c1", "sj2"
  game,        // matches a key in GAME_INFO
  team,        // 3-letter team code
  a, aPos,     // player A name + position
  b, bPos,     // player B name + position
  tier,        // "ELITE" | "STRONG" | "PP LINK"
  conn,        // human label, e.g. "ES L1 + PP1" or "PP1 D-QB"
  corr,        // "Strongest" | "High" | "Moderate" | "Lowest"
  cold,        // boolean — true if either player blanked 2+ consecutive games
  invalid,     // boolean — true if either player is injured / scratched
  top,         // boolean — curated highlight flag (set manually)
  rec,         // boolean — passes ALL 4 Andy Frances rules (see below)
  recR,        // string — one-line reason rec=true, or why it was blocked
  note,        // string — narrative context for the card
}
```

---

## ANDY FRANCES METHODOLOGY (apply every day, no exceptions)

**Tier definitions:**
- ELITE:    ES L1 + PP1 (same even-strength line AND same power play unit)
- STRONG:   ES L1 or ES L2 (same even-strength line, different PP units)
- PP LINK:  Power play connection only (D-QB → F, or F+F on same PP unit)

**Correlation definitions:**
- Strongest: ES L1 + PP1 (share both contexts)
- High:      PP D-QB → F (confirmed D-to-F quarterback chain)
- Moderate:  ES L1 only, or cross-unit even-strength
- Lowest:    PP F+F (5-player dilution, different ES lines)

**4 Rules — a duo gets rec:true ONLY if ALL four pass:**
1. Tier is ELITE or PP LINK (never STRONG)
2. Neither player blanked in their last 2 games
3. Chain overlap or validated D-QB confirmed in the last 3 slates
4. Correlation = Strongest or High (not Moderate, not Lowest)

**Cold flag rule:** Any player who blanked in 2+ consecutive games gets `cold:true`.
Every duo that includes that player also gets `cold:true` and `rec:false`, regardless
of all other factors. Cold flag lifts the next game the player records a point.

**Invalid rule:** Any duo that includes an injured or confirmed-scratch player gets
`invalid:true` and `rec:false`. Annotate the note field with the reason.

---

## SEASON STATS (carry forward — update after you score Apr 7 results)

These are the running totals through Apr 1, 2026. Add Apr 7 results before writing
the new SEASON block. W = duo hit (both players got a point). L = miss. CW = chain
win (goal + primary assist on same chain, scorer + A1 both in the duo).

```
ELITE:    W: 61,  L: 88,  CW: 30   → 41.0%  (Chain OV: 49.2%)
STRONG:   W: 57,  L: 100, CW: 18   → 36.3%  (Chain OV: 31.6%)
PP LINK:  W: 90,  L: 142, CW: 42   → 38.8%  (Chain OV: 46.7%)
TOTAL:    W: 208, L: 330, CW: 90   → 38.7%  (Chain OV: 43.3%)
```

**NOTE:** Apr 2–6 were off-days or non-tracked slates. Apr 7 is the first day with
chain data since Apr 1. Score Apr 7 rec targets before updating SEASON.

---

## APR 7 CARRY-FORWARD: WHAT YOU NEED TO DO FIRST

### Step 1 — Score the Apr 7 Recommended Targets

The Apr 7 rec targets (from the Apr 1 dashboard, applied to the Apr 7 dry-run slate)
were these duos (paste the actual Apr 7 box score data below to confirm):

| ID  | Duo                          | Tier     | Corr      |
|-----|------------------------------|----------|-----------|
| c1  | MacKinnon + Necas (COL)      | ELITE    | Strongest |
| c3  | Toews + MacKinnon (COL PP1)  | PP LINK  | High      |
| a1  | Carlsson + Kreider (ANA)     | ELITE    | Strongest |
| a3  | J.Carlson + L.Carlsson (ANA) | PP LINK  | High      |
| sj1 | Celebrini + W.Smith (SJS)   | ELITE    | Strongest |
| sj2 | Orlov + Celebrini (SJS)     | PP LINK  | High      |

For each: did both players record a point (W)? Was it a direct chain — goal + A1
in the same duo (CW)? Or did neither point (L)?

Write a plain-English performance summary (one sentence per duo) before building
the Apr 8 data block.

### Step 2 — Resolve Cold Flag and Injury Status

**R.Thomas (STL):** The Apr 7 dry-run chain file shows Thomas scored ES in COL@STL
(P1 17:02, assisted by Holloway and Broberg). If the real Apr 7 result confirms this,
Thomas's cold flag IS LIFTED for Apr 8. If the real result shows Thomas was scratched
or did not score/assist, cold flag stays active.

**Makar (COL):** The Apr 7 dry-run chain file shows `MacKinnon,Makar,Necas,PP,P1 5:14`
— Makar credited with an assist. If real Apr 7 confirms this, Makar played and the
UBI designation from Apr 1 should be cleared. For Apr 8: confirm Makar's status from
today's injury report before assigning him any duo. If confirmed active, restore
Makar duos and invalidate any "Toews as PP1 QB" notes — Toews reverts to his normal role.

**Rolling flags — NOT on Apr 8 slate, still tracked:**
- Draisaitl (EDM, LBI): still out, monitor daily
- E.Karlsson (PIT, cold): was cold as of Apr 1, check Apr 7+ results
- M.Schaefer (NYI, cold): was cold as of Apr 1, check Apr 7+ results
- Barzal (NYI, cold): was cold as of Apr 1, check Apr 7+ results

[PASTE APR 7 ACTUAL BOX SCORE DATA HERE — scorer, assists, game type (ES/PP/SH/EN) for all goals]

---

## APR 8 LINE DATA — PASTE BELOW

Paste today's confirmed lines and PP units from DFO (dailyfaceoff.com) or your
line source for all games on the Apr 8 slate.

[PASTE TODAY'S DFO / LINE CONFIRMATION DATA HERE]

**Important:** Do not build Apr 8 duos without confirmed line data. If a player's
line assignment is unconfirmed, mark that duo `invalid:false` but note the uncertainty
in the `note` field and set `rec:false` with a recR explaining the unconfirmed status.

---

## APR 8 GAME SLATE — KNOWN AT TIME OF PROMPT GENERATION

The Apr 8 schedule has not been finalized in this session. Build `GAME_ORDER` and
`GAME_INFO` from the line data you paste above. Use the fields:

```js
GAME_INFO["AWAY@HOME"] = {
  time: "7:00 PM",          // Eastern tip-off
  env: "HIGH" | "MID" | "LOW",  // scoring environment based on O/U and context
  ou: "6.5",                // over/under if available
  context: "...",           // standings position, playoff stakes, injury flags
}
```

**env guide:** HIGH = O/U 6.5+, playoff-stakes, or known high-event matchup.
MID = O/U 5.5–6.0, moderate urgency. LOW = O/U under 5.5, low-event risk.

---

## PRE-PUCK-DROP REFRESH CHECKLIST

> **Run this check 60–90 minutes before the first puck drops on Apr 8.**
> Lines shift late. An undetected scratch or line juggle will invalidate a rec target
> and cost the bet. Do not skip this step even if morning lines looked clean.

- [ ] Pull DFO "Lines" tab for every Apr 8 game — confirm L1/L2/L3 + PP1/PP2 units
- [ ] Cross-check injury report: any new morning skate scratches or late DNP designations?
- [ ] Verify Makar (COL) status: active and on PP1, or still out? If still out, Toews
      remains PP1 QB — confirm Toews duos are valid; invalidate all Makar duos.
- [ ] Verify R.Thomas (STL) is in the lineup if STL is on today's slate.
- [ ] For any duo marked `rec:true`: confirm BOTH players are in the lineup and on the
      same line/unit as the morning data showed.
- [ ] If a pp unit changed hands since morning build (e.g. D-QB swapped), re-evaluate
      all PP LINK duos for that team — demote or invalidate as needed.
- [ ] Update `FETCH_TIME` to the actual time you pulled the final line confirmation.
- [ ] Re-run the rec filter mentally: tier (ELITE or PP LINK) + not cold + not blanked
      last 2 + D-QB confirmed last 3 slates + corr Strongest or High.

---

## YOUR OUTPUT — DELIVER IN THIS ORDER

1. **APR 7 PERFORMANCE SUMMARY**
   Plain English. One sentence per rec target. State: duo name, result (W/L/CW),
   brief note on how points were scored or why they missed.
   Then state the updated SEASON totals (ELITE / STRONG / PP LINK) after adding Apr 7.

2. **COLD FLAG STATUS UPDATE**
   For each tracked cold flag: lifted or still active, and why.

3. **FULL DAILY DATA BLOCK FOR APR 8**
   Drop-in replacement for `NHLTrackerDashboard.jsx`. Format exactly as shown below.
   No extra exports, no renamed fields, no structural changes.

```js
// ─────────────────────────────────────────────────────────────────────────────
//  NHL DUO TRACKER
//  ── DAILY DATA ── Update this section each day via Artifact-Generator
// ─────────────────────────────────────────────────────────────────────────────

export const FETCH_TIME = "[HH:MM ET]";

export const SEASON = {
  ELITE:    { W: ?,  L: ?,  CW: ? },
  STRONG:   { W: ?,  L: ?,  CW: ? },
  "PP LINK":{ W: ?,  L: ?,  CW: ? },
};

export const GAME_ORDER = ["AWAY@HOME", ...];

export const GAME_INFO = {
  "AWAY@HOME": {
    time: "X:XX PM",
    env: "HIGH",
    ou: "6.5",
    context: "...",
  },
  // repeat per game
};

export const DUOS = [
  // ── AWAY @ HOME  X:XX PM ─────────────────────────────────────────────────
  { id:"x1", game:"AWAY@HOME", team:"XXX", a:"LastName", aPos:"C", b:"LastName", bPos:"LW",
    tier:"ELITE",   conn:"ES L1 + PP1",  corr:"Strongest", cold:false, invalid:false, top:true,
    rec:true,
    recR:"ELITE · both L1+PP1 confirmed · neither blanked last 2 · Strongest · chain seen 3 slates",
    note:"Narrative context." },
  // ... all duos for all games
];
```

4. **PRE-PUCK-DROP REFRESH NOTE**
   Restate (do not skip) the items from the checklist above that are most time-sensitive
   given today's specific injury flags and line uncertainty, personalized to Apr 8 context.

---

## REFERENCE: APR 1 DASHBOARD SNAPSHOT (last confirmed real data)

These are the rec targets that were live on Apr 1 (the last real data day). Use as
baseline for chain overlap history when evaluating Apr 8 D-QB chains.

| ID  | Duo                             | Tier     | Corr      | Game    |
|-----|---------------------------------|----------|-----------|---------|
| c1  | MacKinnon + Necas (COL)         | ELITE    | Strongest | VAN@COL |
| c3  | Toews + MacKinnon (COL PP1)     | PP LINK  | High      | VAN@COL |
| a1  | Carlsson + Kreider (ANA)        | ELITE    | Strongest | ANA@SJS |
| a3  | J.Carlson + L.Carlsson (ANA)    | PP LINK  | High      | ANA@SJS |
| sj1 | Celebrini + W.Smith (SJS)      | ELITE    | Strongest | ANA@SJS |
| sj2 | Orlov + Celebrini (SJS)        | PP LINK  | High      | ANA@SJS |

Apr 1 GAME_ORDER was: ["VAN@COL", "STL@LAK", "ANA@SJS"]

Apr 1 STL cold flags: Thomas cold (2+ consecutive blanks) — all Thomas duos had
`cold:true, rec:false`.

Apr 1 COL injury: Makar OUT (UBI) — Makar duo `invalid:true`. Toews assumed PP1 QB role.

---

*Prompt generated: April 8, 2026. File: data/pregame_prompt_apr8_2026.md*
