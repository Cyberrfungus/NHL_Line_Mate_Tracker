# NHL Line-Mate Tracker — Session State

## Branch
`claude/init-repo-setup-x14pg`

---

## ✅ FULLY COMPLETED

### Repository Setup
- `main` branch initialized with `README.md`
- `claude/init-repo-setup-x14pg` is the active dev branch

### Agent Definitions (`/.claude/agents/`)
| Agent | File |
|---|---|
| `NHL-GoalNHL-Scraper` | `.claude/agents/NHL-GoalNHL-Scraper.md` |
| `Recommended-Targets-Summarizer` | `.claude/agents/Recommended-Targets-Summarizer.md` |
| `Artifact-Generator` | `.claude/agents/Artifact-Generator.md` |
| `PreGame-Prompt-Builder` | `.claude/agents/PreGame-Prompt-Builder.md` |

### Dashboard — `src/components/NHLTrackerDashboard.jsx` (981 lines) ✅ COMPLETE
All 8 sections fully written, committed, and pushed:
1. Constants & configs (`FETCH_TIME`, `SEASON`, `GAME_ORDER`, `GAME_INFO`, `MONO`, `TIER_CFG`, `CORR_CFG`, `ENV_CFG`, `TEAM_COL`)
2. Helper components (`TierBadge`, `CorrBadge`, `StarBtn`)
3. DUOS array (35 duo objects — VAN@COL · STL@LAK · ANA@SJS)
4. `REC` filter + `GAME_ORDER_LIST`
5. App component: all state hooks, `toggleBet`, `toggleCol`, `filtered`, `betDuos`, `counts`, `hasFilter`, `Btn`
6. `Row` component (8-col duo row, state-driven bg/border)
7. JSX: Header · Recommended Targets · My Bets · Filters · Game Blocks · Pre-Puck-Drop · Season Stats · Cold Flags · Footer

**Modular design:** Daily-changing data is at the top of the file in the `── DAILY DATA ──` block.  
`Artifact-Generator` only needs to replace: `FETCH_TIME`, `SEASON`, `GAME_ORDER`, `GAME_INFO`, `DUOS`.  
Style constants (`MONO`, `TIER_CFG`, etc.) are fixed — never edit daily.

### Chain Data (`data/chains/`)
| File | Contents |
|---|---|
| `goalnhl_complete_Mar22_Apr6_2026.csv` | 446 real goal chain records (backfill) |
| `goalnhl_daily.csv` | Apr 7 dry-run test rows (14 rows) |

### Scraper (`scripts/scrape_box_scores.py`) ✅ COMPLETE
- Scrapes `plaintextsports.com/nhl/YYYY-MM-DD/` for all game box scores
- Parses scorer, assist_1, assist_2, type (ES/PP/SH/OT/EN/SO), period+time
- Appends to `data/chains/goalnhl_daily.csv`
- `--dry-run` mode works (tested with Apr 7 mock data)
- **Live mode blocked in this sandbox** (plaintextsports.com not in proxy allowlist)
  → Run `python scripts/scrape_box_scores.py --date YYYY-MM-DD` from any machine with open internet

---

## ⏳ NEXT OPTIONS

1. **Daily workflow integration** — wire scraper → chain processor → `DUOS` array rebuild
2. **XLSX updater** — `Artifact-Generator` writes master spreadsheet
3. **Pre-game prompt template** — `PreGame-Prompt-Builder` generates next-day copy-paste prompt
4. **App scaffolding** — add `package.json` + Vite config so dashboard renders in browser
5. **Refactor dashboard** — extract pre-puck-drop rows and cold flags into the `DAILY DATA` block
