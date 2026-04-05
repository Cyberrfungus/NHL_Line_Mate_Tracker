---
name: NHL-GoalNHL-Scraper
description: Autonomously scrapes latest @GoalNHL chains using dev-browser
keywords: goalnhl, chains, scrape, nhl, results
---

You are an expert at using Claude's dev-browser (Playwright) to scrape X/Twitter.

## How @GoalNHL Works

@GoalNHL posts individual goal chains in real time as goals are scored — there is no single daily recap post. To capture a full day's worth of chains you must scrape all posts from @GoalNHL that fall between the first puck drop and the end of the last game on the requested date.

## Task

Given a requested date (YYYY-MM-DD), scrape every @GoalNHL goal chain posted on that date and save the complete set to `data/chains/YYYY-MM-DD.csv`.

## Steps

1. **Search** using X's advanced search operators:
   - Query: `from:GoalNHL since:YYYY-MM-DD until:YYYY-MM-DD+1`
   - Navigate to: `https://x.com/search?q=from%3AGoalNHL+since%3AYYYY-MM-DD+until%3AYYYY-MM-DD%2B1&src=typed_query&f=live`
2. **Scroll** the results page fully — keep scrolling until no new posts load, to ensure all goals from the first puck drop through the end of the last game are captured.
3. **Extract** every chain accurately. Each chain post typically contains:
   - Team abbreviations (official NHL abbreviations only)
   - Scorer name
   - Assist(s) (primary and secondary, if any)
   - Game score at time of goal
   - Period and time of goal
   - Any additional notes (PP, SH, EN, OT, etc.)
4. **Save** results to `data/chains/YYYY-MM-DD.csv` (create the folder if it does not exist) with columns:
   `date, game, team, scorer, assist_1, assist_2, score_at_goal, period, time, notes`

## Rules

- Only scrape real @GoalNHL posts — never hallucinate or infer chains.
- Use official NHL team abbreviations only.
- If a post is ambiguous or malformed, include it with a note in the `notes` column rather than skipping it.
- Return a clean summary: total goals scraped, games covered, and any posts that could not be parsed.
