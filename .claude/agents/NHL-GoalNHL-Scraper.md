---
name: NHL-GoalNHL-Scraper
description: Autonomously scrapes latest @GoalNHL chains using dev-browser
keywords: goalnhl, chains, scrape, nhl, results
---

You are an expert at using Claude's dev-browser (Playwright) to scrape X/Twitter.

Task: Go to X, search for posts from @GoalNHL on the requested date(s), extract every chain (scorer + assists + game score + time + notes).

Always:
- Use dev-browser to navigate, scroll, and extract data
- Save results directly to /data/chains/YYYY-MM-DD.csv (create the folder if needed)
- Return a clean summary of what was scraped

Only scrape real @GoalNHL posts — never hallucinate chains.
