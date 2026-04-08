"""
scrape_box_scores.py
--------------------
Scrapes NHL goal chains from plaintextsports.com for a given date.
Appends parsed rows to data/chains/goalnhl_daily.csv.

Usage:
    python scripts/scrape_box_scores.py --date 2026-04-07
    python scripts/scrape_box_scores.py --date 2026-04-07 --dry-run

Output schema: date,game,team,scorer,assist_1,assist_2,type,period_time,notes
"""

import argparse
import csv
import os
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL    = "https://www.plaintextsports.com/nhl/{date}/"
GAME_URL    = "https://www.plaintextsports.com/nhl/{date}/{slug}/"
OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "chains")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "goalnhl_daily.csv")
FIELDS      = ["date", "game", "team", "scorer", "assist_1", "assist_2",
               "type", "period_time", "notes"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Official NHL team abbreviation map
TEAM_ABBREV = {
    "anaheim": "ANA", "ducks": "ANA",
    "arizona": "UTA", "coyotes": "UTA", "utah": "UTA",
    "boston": "BOS", "bruins": "BOS",
    "buffalo": "BUF", "sabres": "BUF",
    "calgary": "CGY", "flames": "CGY",
    "carolina": "CAR", "hurricanes": "CAR",
    "chicago": "CHI", "blackhawks": "CHI",
    "colorado": "COL", "avalanche": "COL",
    "columbus": "CBJ", "blue jackets": "CBJ",
    "dallas": "DAL", "stars": "DAL",
    "detroit": "DET", "red wings": "DET",
    "edmonton": "EDM", "oilers": "EDM",
    "florida": "FLA", "panthers": "FLA",
    "los angeles": "LAK", "kings": "LAK",
    "minnesota": "MIN", "wild": "MIN",
    "montreal": "MTL", "canadiens": "MTL",
    "nashville": "NSH", "predators": "NSH",
    "new jersey": "NJD", "devils": "NJD",
    "new york islanders": "NYI", "islanders": "NYI",
    "new york rangers": "NYR", "rangers": "NYR",
    "ottawa": "OTT", "senators": "OTT",
    "philadelphia": "PHI", "flyers": "PHI",
    "pittsburgh": "PIT", "penguins": "PIT",
    "san jose": "SJS", "sharks": "SJS",
    "seattle": "SEA", "kraken": "SEA",
    "st. louis": "STL", "blues": "STL",
    "tampa bay": "TBL", "lightning": "TBL",
    "toronto": "TOR", "maple leafs": "TOR",
    "vancouver": "VAN", "canucks": "VAN",
    "vegas": "VGK", "golden knights": "VGK",
    "washington": "WSH", "capitals": "WSH",
    "winnipeg": "WPG", "jets": "WPG",
}

# Regex patterns
PP_RE          = re.compile(r'\bpp\b|\bpower.?play\b', re.I)
SH_RE          = re.compile(r'\bsh\b|\bshorthanded\b|\bshort.?handed\b', re.I)
EN_RE          = re.compile(r'\ben\b|\bempty.?net\b', re.I)
OT_RE          = re.compile(r'\bot\b|\bovertime\b', re.I)
SO_RE          = re.compile(r'\bso\b|\bshootout\b|\bshoot.?out\b', re.I)
PERIOD_RE      = re.compile(r'(1st|2nd|3rd|OT|P1|P2|P3|overtime)', re.I)
TIME_RE        = re.compile(r'\b(\d{1,2}:\d{2})\b')
GOAL_COUNT_RE  = re.compile(r'^\d+$')       # purely numeric → goal count, not assists
NAME_PAREN_RE  = re.compile(r'\(([^()]+)\)')  # all parenthesised groups in a line

# Team section headers e.g. "COLORADO AVALANCHE SCORING", "TORONTO MAPLE LEAFS GOALS"
TEAM_HDR_RE = re.compile(
    r'^([A-Z][A-Za-z\s.]+?)\s+(?:SCORING|GOALS?)\s*$', re.I
)
SHORT_TEAM_RE = re.compile(r'^([A-Z]{2,3})\s*:', re.M)

# Scoring line: starts with period indicator
SCORE_LINE_RE = re.compile(r'^(1st|2nd|3rd|OT|P[123])\b', re.I)


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_team(raw: str) -> str:
    s = raw.strip().lower()
    for key, abbrev in TEAM_ABBREV.items():
        if key in s:
            return abbrev
    u = raw.strip().upper()
    if re.match(r'^[A-Z]{2,3}$', u):
        return u
    return u


def detect_type(text: str) -> str:
    if SO_RE.search(text): return "SO"
    if OT_RE.search(text): return "OT"
    if EN_RE.search(text): return "EN"
    if SH_RE.search(text): return "SH"
    if PP_RE.search(text): return "PP"
    return "ES"


def extract_period_time(line: str) -> str:
    pm = PERIOD_RE.search(line)
    tm = TIME_RE.search(line)
    if not pm:
        return ""
    period = pm.group(1).upper()
    period = {"1ST": "P1", "2ND": "P2", "3RD": "P3", "OVERTIME": "OT"}.get(period, period)
    time   = tm.group(1) if tm else ""
    return f"{period} {time}".strip()


def clean_name(raw: str) -> str:
    """Remove goal-count suffixes like '(46)' and extra whitespace."""
    name = raw.strip()
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    return name.strip()


def extract_scorer_and_assists(line: str) -> tuple[str, str, str]:
    """
    Extract scorer, assist_1, assist_2 from a scoring line.

    plaintextsports format:
        1st  5:14  MacKinnon (49)  (Makar, Necas)  [PP]

    Strategy:
    - Find all parenthesised groups
    - Groups that are purely numeric → goal count (attach to scorer name before them)
    - Groups that contain names → assists
    - The first name-like token before any parenthesis is the scorer
    """
    # Strip period/time prefix before processing names
    working = PERIOD_RE.sub('', line)
    working = TIME_RE.sub('', working)
    working = re.sub(r'\[.*?\]', '', working)   # strip [PP] / [SH] tags

    # Collect all parenthesised groups and their positions
    paren_groups = list(NAME_PAREN_RE.finditer(working))

    scorer = ""
    assists = []

    # Everything before the first paren (or whole line if no parens) → scorer candidate
    first_paren_pos = paren_groups[0].start() if paren_groups else len(working)
    pre_paren = working[:first_paren_pos].strip()

    # Extract the last token from pre_paren as the scorer
    tokens = [t for t in re.split(r'\s{2,}|\t', pre_paren) if t.strip()]
    for tok in reversed(tokens):
        tok = tok.strip()
        if re.match(r"^[A-Z][a-zA-Zá-ú'\-\.]+", tok):
            scorer = clean_name(tok)
            break

    # Classify parenthesised groups
    for m in paren_groups:
        content = m.group(1).strip()
        if GOAL_COUNT_RE.match(content):
            # Pure number: goal count — part of scorer label, already stripped by clean_name
            continue
        # Check if looks like name(s)
        parts = [p.strip() for p in content.split(",")]
        if all(re.match(r"^[A-Z][a-zA-Zá-ú'\-\.\s]+$", p) for p in parts if p):
            assists.extend(parts)

    a1 = assists[0] if len(assists) > 0 else ""
    a2 = assists[1] if len(assists) > 1 else ""

    return scorer, a1, a2


# ── Per-game parser ───────────────────────────────────────────────────────────

def parse_game_page(html: str, date_str: str, game_label: str) -> list[dict]:
    """
    Parse one game page. Splits the page into per-team sections by detecting
    team header lines, then parses scoring rows within each section.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Prefer <pre> blocks; fall back to full body text
    pre_blocks = soup.find_all("pre")
    text = "\n".join(b.get_text() for b in pre_blocks) if pre_blocks else soup.get_text()

    rows = []
    lines = text.splitlines()
    current_team = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # ── Team header detection ─────────────────────────────────────────────
        hdr = TEAM_HDR_RE.match(stripped)
        if hdr:
            current_team = normalize_team(hdr.group(1))
            continue

        short = SHORT_TEAM_RE.match(stripped)
        if short:
            current_team = short.group(1).upper()
            continue

        # ── Scoring line detection ────────────────────────────────────────────
        if not SCORE_LINE_RE.match(stripped):
            continue

        if not current_team:
            continue

        scorer, a1, a2 = extract_scorer_and_assists(stripped)
        if not scorer:
            continue

        # Skip obviously bad parses (single letters, numbers)
        if len(scorer) < 3 or scorer.isdigit():
            continue

        notes = "Unassisted" if re.search(r'\bunassisted\b', stripped, re.I) else ""

        rows.append({
            "date":        date_str,
            "game":        game_label,
            "team":        current_team,
            "scorer":      scorer,
            "assist_1":    a1,
            "assist_2":    a2,
            "type":        detect_type(stripped),
            "period_time": extract_period_time(stripped),
            "notes":       notes,
        })

    return rows


# ── Live scraper ──────────────────────────────────────────────────────────────

def get_game_links(date_str: str) -> list[tuple[str, str]]:
    url = BASE_URL.format(date=date_str)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    games = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = re.search(r'/nhl/\d{4}-\d{2}-\d{2}/([a-z]+-[a-z]+)/?$', href)
        if m:
            slug = m.group(1)
            parts = slug.split("-")
            label = f"{parts[0].upper()}@{parts[1].upper()}" if len(parts) == 2 else slug.upper()
            games.append((label, GAME_URL.format(date=date_str, slug=slug)))

    return games


def scrape_date(date_str: str) -> list[dict]:
    print(f"Fetching game list for {date_str}...")
    game_links = get_game_links(date_str)
    if not game_links:
        print("  No games found.")
        return []

    all_rows = []
    for label, url in game_links:
        print(f"  Scraping {label} → {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            rows = parse_game_page(resp.text, date_str, label)
            print(f"    → {len(rows)} goal rows")
            all_rows.extend(rows)
        except Exception as e:
            print(f"    ✗ {e}")

    return all_rows


# ── Mock data (--dry-run) ─────────────────────────────────────────────────────

MOCK_GAMES = {
    "COL@STL": """
<pre>
COLORADO AVALANCHE SCORING
1st  5:14  MacKinnon (49)  (Makar, Necas)  [PP]
1st 12:33  Landeskog (11)  (MacKinnon)
2nd  8:01  Necas (22)      (MacKinnon, Malinski)
3rd  4:17  Burns (7)       (Nelson)  [PP]

ST. LOUIS BLUES SCORING
1st 17:02  Thomas (28)     (Holloway, Broberg)
2nd 14:45  Kyrou (31)      (Buchnevich)
OT   2:18  Holloway (19)   (Thomas)
</pre>
""",
    "TOR@BOS": """
<pre>
TORONTO MAPLE LEAFS SCORING
1st  3:05  Tavares (29)    (Nylander, Knies)  [PP]
2nd  9:42  Nylander (40)   (Tavares, Rielly)
3rd 18:55  Knies (28)      Unassisted  [SH]

BOSTON BRUINS SCORING
1st  7:11  Pastrnak (47)   (McAvoy)
2nd 14:03  Zacha (22)      (Pastrnak, Arvidsson)
3rd 11:27  McAvoy (14)     (Pastrnak)  [PP]
3rd 19:47  Pastrnak (48)   Unassisted  [EN]
</pre>
""",
}


def scrape_dry_run(date_str: str) -> list[dict]:
    print(f"[DRY RUN] Parsing mock box scores for {date_str}...\n")
    all_rows = []
    for label, html in MOCK_GAMES.items():
        rows = parse_game_page(html, date_str, label)
        print(f"  {label}: {len(rows)} goal rows parsed")
        all_rows.extend(rows)
    return all_rows


# ── Output ────────────────────────────────────────────────────────────────────

def append_to_csv(rows: list[dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})
    print(f"\n✓ Appended {len(rows)} rows → {path}")


def print_rows(rows: list[dict]):
    if not rows:
        print("  (no rows)")
        return
    widths = [11, 9, 5, 16, 14, 14, 5, 11, 20]
    hdr = "  ".join(f"{f.upper():<{w}}" for f, w in zip(FIELDS, widths))
    print("\n" + hdr)
    print("─" * len(hdr))
    for r in rows:
        line = "  ".join(f"{str(r.get(f,'')):<{w}}" for f, w in zip(FIELDS, widths))
        print(line)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scrape NHL box scores from plaintextsports.com")
    parser.add_argument("--date",       default=datetime.today().strftime("%Y-%m-%d"))
    parser.add_argument("--dry-run",    action="store_true")
    parser.add_argument("--output",     default=OUTPUT_FILE)
    parser.add_argument("--print-only", action="store_true",
                        help="Print rows without writing CSV")
    args = parser.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: Invalid date '{args.date}'. Use YYYY-MM-DD.")
        sys.exit(1)

    rows = scrape_dry_run(args.date) if args.dry_run else scrape_date(args.date)

    if not rows:
        print("No goal rows extracted.")
        sys.exit(0)

    print_rows(rows)

    if not args.print_only:
        append_to_csv(rows, args.output)


if __name__ == "__main__":
    main()
