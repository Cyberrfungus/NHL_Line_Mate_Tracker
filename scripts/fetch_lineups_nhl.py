#!/usr/bin/env python3
"""
fetch_lineups_nhl.py - Fetch NHL lineups from DFO + NHL.com fallback.

v3 (2026-04-19): Rewritten against DFO's real __NEXT_DATA__ schema.

DFO schema (verified from live debug dump):
    props.pageProps.combinations.players[]
    each player has:
        name                 - "Nathan MacKinnon"
        positionIdentifier   - "lw" | "c" | "rw" | "ld" | "rd" | "g1" | "g2" | "sk1..5"
        groupIdentifier      - "f1" | "f2" | "f3" | "f4" | "d1" | "d2" | "d3"
                               | "pp1" | "pp2" | "pk1" | "pk2" | "g" | "ir"
        injuryStatus         - null | "dtd" | "ir" | ...
        gameTimeDecision     - bool
        latestNews.details   - text

Players appear MULTIPLE times (one entry per group they're in).
We dedupe by group and build L1-L4, D1-D3, PP1, PP2, goalies, scratches, injuries.

Usage:
    py scripts/fetch_lineups_nhl.py
    py scripts/fetch_lineups_nhl.py --date 2026-04-19
    py scripts/fetch_lineups_nhl.py --debug
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import date, datetime

try:
    import requests
except ImportError:
    print("ERROR: Missing 'requests'. Install with:  py -m pip install requests")
    sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

NHL_API = "https://api-web.nhle.com"

TEAM_MAP = {
    "ANA": "ANA", "BOS": "BOS", "BUF": "BUF", "CGY": "CGY", "CAR": "CAR",
    "CHI": "CHI", "COL": "COL", "CBJ": "CBJ", "DAL": "DAL", "DET": "DET",
    "EDM": "EDM", "FLA": "FLA", "LAK": "LAK", "MIN": "MIN", "MTL": "MTL",
    "NSH": "NSH", "NJD": "NJD", "NYI": "NYI", "NYR": "NYR", "OTT": "OTT",
    "PHI": "PHI", "PIT": "PIT", "SJS": "SJS", "SEA": "SEA", "STL": "STL",
    "TBL": "TBL", "TOR": "TOR", "UTA": "UTA", "VAN": "VAN", "VGK": "VGK",
    "WPG": "WPG", "WSH": "WSH",
    # alternates
    "LA": "LAK", "NJ": "NJD", "SJ": "SJS", "TB": "TBL", "VEG": "VGK",
    "MON": "MTL", "NAS": "NSH", "WAS": "WSH", "ARI": "UTA",
}

TEAM_SLUGS = {
    "ANA": "anaheim-ducks", "BOS": "boston-bruins", "BUF": "buffalo-sabres",
    "CGY": "calgary-flames", "CAR": "carolina-hurricanes", "CHI": "chicago-blackhawks",
    "COL": "colorado-avalanche", "CBJ": "columbus-blue-jackets", "DAL": "dallas-stars",
    "DET": "detroit-red-wings", "EDM": "edmonton-oilers", "FLA": "florida-panthers",
    "LAK": "los-angeles-kings", "MIN": "minnesota-wild", "MTL": "montreal-canadiens",
    "NSH": "nashville-predators", "NJD": "new-jersey-devils", "NYI": "new-york-islanders",
    "NYR": "new-york-rangers", "OTT": "ottawa-senators", "PHI": "philadelphia-flyers",
    "PIT": "pittsburgh-penguins", "SJS": "san-jose-sharks", "SEA": "seattle-kraken",
    "STL": "st-louis-blues", "TBL": "tampa-bay-lightning", "TOR": "toronto-maple-leafs",
    "UTA": "utah-mammoth", "VAN": "vancouver-canucks", "VGK": "vegas-golden-knights",
    "WPG": "winnipeg-jets", "WSH": "washington-capitals",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

DEBUG = False


def dprint(*args):
    if DEBUG:
        print("  [debug]", *args)


# ---------------------------------------------------------------------------
# NHL schedule
# ---------------------------------------------------------------------------
def get_schedule(target_date, session):
    url = f"{NHL_API}/v1/schedule/{target_date}"
    try:
        resp = session.get(url, timeout=15)
        data = resp.json()
        games = []
        for day in data.get("gameWeek", []):
            if day.get("date") == target_date:
                for game in day.get("games", []):
                    away = TEAM_MAP.get(game.get("awayTeam", {}).get("abbrev", ""), "")
                    home = TEAM_MAP.get(game.get("homeTeam", {}).get("abbrev", ""), "")
                    if away and home:
                        games.append({
                            "away": away, "home": home,
                            "game_id": game.get("id"),
                            "start": game.get("startTimeUTC", ""),
                        })
        return games
    except Exception as e:
        print(f"  Schedule API error: {e}")
        return []


# ---------------------------------------------------------------------------
# DFO parser - matches verified schema
# ---------------------------------------------------------------------------
FWD_POS_ORDER = {"lw": 0, "c": 1, "rw": 2}
D_POS_ORDER = {"ld": 0, "rd": 1}


def _sort_sk(entries):
    def key(e):
        m = re.match(r"sk(\d+)", e["pos"])
        return int(m.group(1)) if m else 99
    return sorted(entries, key=key)


def parse_dfo_combinations(combinations):
    """Take combinations dict from DFO __NEXT_DATA__ and produce lineup entry."""
    players = combinations.get("players", [])
    if not players:
        return None

    groups = {}
    injuries = []

    for p in players:
        gid = p.get("groupIdentifier")
        name = (p.get("name") or "").strip()
        if not name:
            continue
        pos = (p.get("positionIdentifier") or "").lower()
        inj = p.get("injuryStatus")
        gtd = bool(p.get("gameTimeDecision"))

        if gid == "ir":
            note = ""
            ln = p.get("latestNews") or {}
            if isinstance(ln, dict):
                note = (ln.get("details") or "").strip()
            injuries.append({
                "player": name,
                "status": inj or "dtd",
                "note": note,
                "game_time_decision": gtd,
            })
            continue

        if not gid:
            continue

        groups.setdefault(gid, []).append({
            "name": name, "pos": pos, "inj": inj, "gtd": gtd,
        })

    entry = {
        "updated": datetime.now().isoformat(),
        "source": "DFO-nextdata",
        "source_updated": combinations.get("updatedAt", ""),
        "team_id": combinations.get("teamId"),
    }

    # Forward lines
    for i in range(1, 5):
        gid = f"f{i}"
        if gid in groups:
            ordered = sorted(groups[gid], key=lambda e: FWD_POS_ORDER.get(e["pos"], 99))
            entry[f"L{i}"] = [e["name"] for e in ordered]
        else:
            entry[f"L{i}"] = []

    # Defense pairs
    for i in range(1, 4):
        gid = f"d{i}"
        if gid in groups:
            ordered = sorted(groups[gid], key=lambda e: D_POS_ORDER.get(e["pos"], 99))
            entry[f"D{i}"] = [e["name"] for e in ordered]
        else:
            entry[f"D{i}"] = []

    # Power play
    for i in range(1, 3):
        gid = f"pp{i}"
        if gid in groups:
            entry[f"PP{i}"] = [e["name"] for e in _sort_sk(groups[gid])]
        else:
            entry[f"PP{i}"] = []

    # Penalty kill
    for i in range(1, 3):
        gid = f"pk{i}"
        if gid in groups:
            entry[f"PK{i}"] = [e["name"] for e in _sort_sk(groups[gid])]
        else:
            entry[f"PK{i}"] = []

    # Goalies
    if "g" in groups:
        gs = groups["g"]
        entry["starter"] = next((g["name"] for g in gs if g["pos"] == "g1"), None)
        entry["backup"] = next((g["name"] for g in gs if g["pos"] == "g2"), None)
    else:
        entry["starter"] = None
        entry["backup"] = None

    entry["injuries"] = injuries
    entry["scratched"] = []

    if len(entry["L1"]) < 2 or len(entry["L2"]) < 2 or len(entry["D1"]) < 1:
        return None
    return entry


def fetch_dfo_structured(team_code, session):
    slug = TEAM_SLUGS.get(team_code)
    if not slug:
        return None

    url = f"https://www.dailyfaceoff.com/teams/{slug}/line-combinations"
    try:
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            dprint(f"{team_code}: status {resp.status_code}")
            return None

        m = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            resp.text, re.DOTALL
        )
        if not m:
            dprint(f"{team_code}: no __NEXT_DATA__")
            return None

        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            dprint(f"{team_code}: JSON decode: {e}")
            return None

        if DEBUG:
            dump = os.path.join(DATA_DIR, f"_debug_{team_code}_nextdata.json")
            with open(dump, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        combinations = (
            data.get("props", {})
                .get("pageProps", {})
                .get("combinations")
        )
        if not combinations:
            dprint(f"{team_code}: no combinations block")
            return None

        return parse_dfo_combinations(combinations)

    except Exception as e:
        dprint(f"{team_code}: exception {e}")
        return None


# ---------------------------------------------------------------------------
# NHL.com preview fallback
# ---------------------------------------------------------------------------
NAME_BLOCKLIST_LOWER = {
    "hockey with an accent", "starting goalies", "line combination",
    "line combinations", "daily faceoff", "power play", "penalty kill",
    "projected lineup", "scratched injured", "stanley cup", "game preview",
    "click here", "read more", "team news", "season stats", "last game",
    "show jerseys", "hide news", "news indicator", "fantasy hockey",
    "draft lottery", "lottery odds", "nhl draft", "daily face off",
    "nhl network", "sportsnet", "tnt sports",
}

NAME_BAD_SUBSTRINGS = {
    "accent", "hockey", "goalies", "combination", "combinations", "news",
    "stats", "jerseys", "faceoff", "fantasy", "penalty", "powerplay",
    "defensive", "forward", "lottery", "draft", "schedule", "weekly",
    "rankings", "click", "preview", "lineup", "sportsnet", "network",
    "starting", "projected",
}


def is_valid_player_name(n):
    if not n:
        return False
    n = n.strip()
    if len(n) <= 3 or len(n) > 40:
        return False
    if n.lower() in NAME_BLOCKLIST_LOWER:
        return False
    lower = n.lower()
    if any(w in lower for w in NAME_BAD_SUBSTRINGS):
        return False
    if " " not in n:
        return False
    for tok in n.split():
        if not tok:
            return False
        if not (tok[0].isupper() or tok[0] in "'-"):
            return False
    return True


def build_preview_urls(away, home, target_date):
    a = TEAM_SLUGS.get(away, away.lower())
    h = TEAM_SLUGS.get(home, home.lower())
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    month = dt.strftime("%B").lower()
    return [
        f"https://www.nhl.com/news/{a}-{h}-game-preview-{month}-{dt.day}-{dt.year}",
        f"https://www.nhl.com/news/{h}-{a}-game-preview-{month}-{dt.day}-{dt.year}",
    ]


def parse_preview_text(text, team_code):
    entry = {
        "updated": datetime.now().isoformat(),
        "source": "NHL.com-preview",
        "injuries": [], "scratched": [],
        "PP1": [], "PP2": [], "PK1": [], "PK2": [],
        "starter": None, "backup": None,
    }
    slug_words = TEAM_SLUGS.get(team_code, "").replace("-", " ").split()
    if not slug_words:
        return None
    team_tail = " ".join(slug_words[-2:]) if len(slug_words) >= 2 else slug_words[-1]

    pat = re.compile(
        rf"{re.escape(team_tail)}\s+projected\s+lineup(.+?)(?:projected\s+lineup|$)",
        re.IGNORECASE | re.DOTALL,
    )
    m = pat.search(text)
    if not m:
        return None
    section = m.group(1)
    for stop in ("Status report", "Season series", "Last 10"):
        idx = section.lower().find(stop.lower())
        if idx != -1:
            section = section[:idx]
            break

    trio_re = re.compile(
        r"([A-Z][A-Za-z'\.\-]+(?:\s+[A-Z][A-Za-z'\.\-]+)+)\s*[-\u2013\u2014]{1,2}\s*"
        r"([A-Z][A-Za-z'\.\-]+(?:\s+[A-Z][A-Za-z'\.\-]+)+)\s*[-\u2013\u2014]{1,2}\s*"
        r"([A-Z][A-Za-z'\.\-]+(?:\s+[A-Z][A-Za-z'\.\-]+)+)"
    )
    pair_re = re.compile(
        r"([A-Z][A-Za-z'\.\-]+(?:\s+[A-Z][A-Za-z'\.\-]+)+)\s*[-\u2013\u2014]{1,2}\s*"
        r"([A-Z][A-Za-z'\.\-]+(?:\s+[A-Z][A-Za-z'\.\-]+)+)(?!\s*[-\u2013\u2014])"
    )

    trios = []
    for tri in trio_re.finditer(section):
        names = [tri.group(i).strip() for i in (1, 2, 3)]
        if all(is_valid_player_name(n) for n in names):
            trios.append(names)
            if len(trios) >= 4:
                break

    section_trimmed = trio_re.sub("", section)
    pairs = []
    for pr in pair_re.finditer(section_trimmed):
        names = [pr.group(i).strip() for i in (1, 2)]
        if all(is_valid_player_name(n) for n in names):
            pairs.append(names)
            if len(pairs) >= 3:
                break

    for i in range(4):
        entry[f"L{i+1}"] = trios[i] if i < len(trios) else []
    for i in range(3):
        entry[f"D{i+1}"] = pairs[i] if i < len(pairs) else []

    if sum(1 for k in ("L1", "L2", "L3", "L4") if entry[k]) < 2:
        return None
    if sum(1 for k in ("D1", "D2", "D3") if entry[k]) < 1:
        return None
    return entry


def fetch_game_preview(away, home, target_date, session):
    for url in build_preview_urls(away, home, target_date):
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code != 200:
                continue
            results = {}
            for code in (away, home):
                e = parse_preview_text(resp.text, code)
                if e:
                    results[code] = e
            if results:
                return results, url
        except Exception as e:
            dprint(f"preview {url}: {e}")
            continue
    return {}, None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
KNOWN_DEFENSEMEN = {
    "Cale Makar", "Devon Toews", "Quinn Hughes", "Rasmus Dahlin",
    "Mikhail Sergachev", "Nate Schmidt", "Victor Hedman", "Roman Josi",
    "Adam Fox", "Jaccob Slavin", "Noah Hanifin", "Drew Doughty",
    "Josh Morrissey", "Brent Burns", "Kris Letang", "Miro Heiskanen",
    "Evan Bouchard", "Brandt Clarke", "Mikey Anderson", "Erik Karlsson",
    "Lane Hutson", "Hampus Lindholm", "Brett Kulak", "Josh Manson",
    "Sam Malinski",
}

KNOWN_FORWARDS = {
    "Nathan MacKinnon", "Connor McDavid", "Leon Draisaitl",
    "Nikita Kucherov", "Brayden Point", "Jonathan Toews",
    "Artemi Panarin", "Anze Kopitar", "Adrian Kempe",
    "Jake Guentzel", "Brad Marchand", "Sidney Crosby",
    "Evgeni Malkin", "Clayton Keller", "Nick Schmaltz",
    "Logan Cooley", "Dylan Guenther", "Jason Robertson",
    "Roope Hintz", "Tage Thompson", "Alex Tuch", "Mitch Marner",
    "Auston Matthews", "William Nylander", "Cole Caufield",
    "Nick Suzuki", "Juraj Slafkovsky", "Jack Hughes", "Jesper Bratt",
    "Kirill Kaprizov", "Matt Boldy", "Joel Eriksson Ek",
    "Wyatt Johnston", "Matt Duchene", "Trevor Zegras",
    "Owen Tippett", "Bryan Rust", "Andrei Svechnikov",
    "Cole Perfetti", "Mathew Barzal", "Bo Horvat",
    "Quinton Byfield", "Martin Necas", "Nazem Kadri",
    "Brock Nelson", "Gabriel Landeskog", "Artturi Lehkonen",
    "Valeri Nichushkin", "Mark Stone", "Morgan Geekie",
    "Jason Zucker",
}


def validate_entry(team, entry):
    warns = []
    for lk in ("L1", "L2", "L3", "L4"):
        for name in entry.get(lk, []):
            if name in KNOWN_DEFENSEMEN:
                warns.append(f"{team}: {name} (D) listed in {lk}")
    for dk in ("D1", "D2", "D3"):
        for name in entry.get(dk, []):
            if name in KNOWN_FORWARDS:
                warns.append(f"{team}: {name} (F) listed in {dk}")

    all_es = []
    for k in ("L1", "L2", "L3", "L4", "D1", "D2", "D3"):
        all_es.extend(entry.get(k, []))
    dupes = {n for n in all_es if all_es.count(n) > 1}
    if dupes:
        warns.append(f"{team}: duplicate ES names {sorted(dupes)}")

    for pk in ("PP1", "PP2"):
        unit = entry.get(pk, [])
        if len(unit) != len(set(unit)):
            warns.append(f"{team}: duplicate in {pk} {unit}")

    if len(entry.get("L1", [])) < 3:
        warns.append(f"{team}: L1 has only {len(entry.get('L1', []))} players")

    return warns


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    global DEBUG
    parser = argparse.ArgumentParser(description="Fetch NHL lineups (DFO JSON + NHL.com fallback)")
    parser.add_argument("--date", default=None)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    DEBUG = args.debug
    target_date = args.date or date.today().strftime("%Y-%m-%d")
    out_path = os.path.join(DATA_DIR, f"lineups_{target_date}.json")

    session = requests.Session()
    session.headers.update(HEADERS)

    print(f"Fetching schedule for {target_date}...")
    games = get_schedule(target_date, session)
    if not games:
        print("No games found.")
        sys.exit(1)

    print(f"Found {len(games)} games:")
    for g in games:
        print(f"  {g['away']} @ {g['home']}")
    print()

    results = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception:
            results = {}

    playing = set()
    for g in games:
        playing.add(g["away"])
        playing.add(g["home"])

    # Step 1: DFO structured
    print("=== DFO (structured JSON) ===")
    for team in sorted(playing):
        print(f"  {team}...", end=" ", flush=True)
        entry = fetch_dfo_structured(team, session)
        if entry:
            results[team] = entry
            n = sum(len(entry.get(k, [])) for k in
                    ("L1", "L2", "L3", "L4", "D1", "D2", "D3", "PP1", "PP2"))
            g_starter = entry.get("starter") or "?"
            print(f"OK ({n} slots, G:{g_starter})")
        else:
            print("FAILED")
        time.sleep(0.5)

    # Step 2: NHL.com fallback
    def needs_fallback(team):
        e = results.get(team)
        if not e:
            return True
        if len(e.get("L1", [])) < 3 or len(e.get("L2", [])) < 3:
            return True
        return False

    missing = [t for t in playing if needs_fallback(t)]
    if missing:
        print(f"\n=== NHL.com preview fallback (needed: {', '.join(missing)}) ===")
        for g in games:
            if g["away"] in missing or g["home"] in missing:
                print(f"  {g['away']}@{g['home']}...", end=" ", flush=True)
                prev, url = fetch_game_preview(g["away"], g["home"], target_date, session)
                if prev:
                    for team, entry in prev.items():
                        if team in missing:
                            results[team] = entry
                            n = sum(len(entry.get(k, [])) for k in ("L1", "L2", "L3", "L4", "D1", "D2", "D3"))
                            print(f"{team}:OK({n})", end=" ")
                    print()
                else:
                    print("NONE")
                time.sleep(1)

    # Step 3: validation
    print("\n=== Validation ===")
    all_warns = []
    for team in sorted(results):
        all_warns.extend(validate_entry(team, results[team]))
    if all_warns:
        print("WARNINGS DETECTED - review before using:")
        for w in all_warns:
            print(f"   {w}")
    else:
        print("No obvious errors.")

    results = dict(sorted(results.items()))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    still_missing = [t for t in playing if t not in results or not results[t].get("L1")]
    success = len(playing) - len(still_missing)
    print(f"\nDone: {success}/{len(playing)} teams")
    if still_missing:
        print(f"Missing: {', '.join(still_missing)}")
    print(f"Saved: {out_path}")

    if all_warns:
        sys.exit(2)


if __name__ == "__main__":
    main()
