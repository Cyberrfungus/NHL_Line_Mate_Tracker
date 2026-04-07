# NHL Line-Mate Tracker — Session State

## Current Task
Writing `src/components/NHLTrackerDashboard.jsx` — full modular React dashboard component.

## Status
- File exists at `src/components/NHLTrackerDashboard.jsx` but contains only a placeholder (`test`).
- Component has NOT been written yet.

## What To Build
Modular NHL Tracker Dashboard based on `nhl_tracker_apr01_2026.jsx` style. Key sections:

1. **Header** — date label, fetch time, slate summary (games / active duos / targets count)
2. **Recommended Targets** — filtered duos passing all 4 rules, with tier/corr badges + reason
3. **My Bets** — star-toggled duos displayed as compact chips with a "Bets Only" filter
4. **Filters** — tier, game, team, correlation, player search, bets-only toggle
5. **Game Blocks** — collapsible per-game sections with top-play strip + full duo rows
6. **Pre-Puck-Drop Refresh** — checklist items (tag / status / observation)
7. **Season Stats** — W/L/CW per tier with progress bars
8. **Cold Flags** — active cold/injury flags table

## Modular Design Rule
Daily-changing data lives at the TOP of the file in a clearly delimited `── DAILY DATA ──` block:
- `METADATA` (date string, fetch time, slate description)
- `SEASON` (W/L/CW per tier)
- `GAME_INFO` (per-game time, env, O/U, context)
- `GAME_ORDER` (array of game keys)
- `DUOS` (full duo array)
- `PRE_PUCK_DROP_ITEMS` (checklist rows)
- `COLD_FLAGS` (active flags)

The Artifact-Generator agent only needs to replace this block.

## Style Constants (fixed, never change)
- Dark bg: `#04060C`
- Monospace font: JetBrains Mono / Fira Code / Courier New
- Tier colors: ELITE=green, STRONG=blue, PP LINK=amber
- Corr colors: Strongest=green, High=lime, Moderate=yellow, Lowest=red
- Team colors keyed by abbreviation

## Branch
`claude/init-repo-setup-x14pg`

## Next Steps
1. Write the full JSX component (all sections above)
2. Commit & push to branch
