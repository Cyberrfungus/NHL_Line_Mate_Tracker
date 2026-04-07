# NHL Line-Mate Tracker — Session State

## Branch
`claude/init-repo-setup-x14pg`

---

## ✅ COMPLETED

### NHLTrackerDashboard.jsx — COMPLETE (981 lines)
`src/components/NHLTrackerDashboard.jsx`

All 8 sections from original `nhl_tracker_apr01_2026.jsx` template:

1. **Constants & configs** — `FETCH_TIME`, `SEASON`, `GAME_ORDER`, `GAME_INFO`, `MONO`, `TIER_CFG`, `CORR_CFG`, `ENV_CFG`, `TEAM_COL`
2. **Helper components** — `TierBadge`, `CorrBadge`, `StarBtn`
3. **DUOS array** — 35 duo objects across VAN@COL · STL@LAK · ANA@SJS
4. **REC filter** — `DUOS.filter(d => d.rec && !d.cold && !d.invalid)` → 5 targets
5. **App component state** — `tierF/teamF/gameF/corrF/search/betsOnly/myBets/collapsed`, `toggleBet`, `toggleCol`, `teams`, `filtered`, `betDuos`, `counts`, `hasFilter`, `Btn`
6. **Row component** — 8-col duo row with state-driven bg/border colors
7. **Header** — title, fetch time, counts, 5 stat boxes
8. **Recommended Targets** — green box, 4 rules, REC.map() table
9. **My Bets** — conditional gold box, bet pills, BETS ONLY toggle
10. **Filters** — tier/corr row, game row, team row + search + bets toggle
11. **Game Blocks** — collapsible per-game divs with TOP strip, col headers, Row components
12. **Pre-Puck-Drop Refresh** — 7-row checklist, status color logic
13. **Season Stats** — ELITE/STRONG/PP LINK/TOTAL cards with W% bar + chain OV%
14. **Cold Flags** — 7-row rolling cold/injury table
15. **Footer** — date · fetch time · methodology · disclaimer

### Modular Design Rule (for Artifact-Generator)
Daily-changing data lives at the TOP of the file in the `── DAILY DATA ──` block:
- `FETCH_TIME` — lines fetch timestamp
- `SEASON` — W/L/CW per tier
- `GAME_ORDER` — ordered array of game keys
- `GAME_INFO` — per-game time, env, O/U, context string
- `DUOS` — full 35-object array (replace entirely each day)
- Pre-puck-drop rows and cold flags are hardcoded inline (move to constants in future refactor)

Style constants (`MONO`, `TIER_CFG`, `CORR_CFG`, `ENV_CFG`, `TEAM_COL`) are fixed — never edit daily.

### Agents Defined
| Agent | File |
|---|---|
| `NHL-GoalNHL-Scraper` | `.claude/agents/NHL-GoalNHL-Scraper.md` |
| `Recommended-Targets-Summarizer` | `.claude/agents/Recommended-Targets-Summarizer.md` |
| `Artifact-Generator` | `.claude/agents/Artifact-Generator.md` |
| `PreGame-Prompt-Builder` | `.claude/agents/PreGame-Prompt-Builder.md` |

---

## ⏳ NEXT

Possible next steps (confirm with user):

1. **Daily data ingestion** — wire `NHL-GoalNHL-Scraper` output (`data/chains/YYYY-MM-DD.csv`) into a processing script that rebuilds the `DUOS` array
2. **XLSX updater** — `Artifact-Generator` updates master spreadsheet with new chain data + recommended targets
3. **Pre-game prompt template** — `PreGame-Prompt-Builder` generates copy-paste prompt for next day
4. **App scaffolding** — add `package.json`, Vite/CRA config so dashboard renders in browser
5. **Refactor** — extract pre-puck-drop rows and cold flags into `DAILY DATA` block constants
