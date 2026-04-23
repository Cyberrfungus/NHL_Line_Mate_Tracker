"""
fetch_goalies.py v2 - Scrape DFO Starting Goalies via __NEXT_DATA__ JSON blob
Usage: py scripts/fetch_goalies.py --date 2026-04-16 [--raw-html]

Outputs: data/goalies_YYYY-MM-DD.json
"""

import argparse, json, re, sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Missing deps. Run: py -m pip install requests")
    sys.exit(1)

SLUG_TO_ABBR = {
    "anaheim-ducks": "ANA", "boston-bruins": "BOS", "buffalo-sabres": "BUF",
    "calgary-flames": "CGY", "carolina-hurricanes": "CAR", "chicago-blackhawks": "CHI",
    "colorado-avalanche": "COL", "columbus-blue-jackets": "CBJ", "dallas-stars": "DAL",
    "detroit-red-wings": "DET", "edmonton-oilers": "EDM", "florida-panthers": "FLA",
    "los-angeles-kings": "LAK", "minnesota-wild": "MIN", "montreal-canadiens": "MTL",
    "nashville-predators": "NSH", "new-jersey-devils": "NJD", "new-york-islanders": "NYI",
    "new-york-rangers": "NYR", "ottawa-senators": "OTT", "philadelphia-flyers": "PHI",
    "pittsburgh-penguins": "PIT", "san-jose-sharks": "SJS", "seattle-kraken": "SEA",
    "st-louis-blues": "STL", "tampa-bay-lightning": "TBL",
    "toronto-maple-leafs": "TOR", "utah-mammoth": "UTA", "utah-hockey-club": "UTA",
    "vancouver-canucks": "VAN", "vegas-golden-knights": "VGK",
    "washington-capitals": "WSH", "winnipeg-jets": "WPG",
}


def fetch_dfo():
    r = requests.get(
        "https://www.dailyfaceoff.com/starting-goalies",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.text


def extract_next_data(html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', html, re.S)
    if not m:
        raise RuntimeError("__NEXT_DATA__ blob not found in HTML")
    return json.loads(m.group(1))


def parse_goalies(next_data):
    games = next_data["props"]["pageProps"]["data"]
    result = {}

    for g in games:
        home_slug = g.get("homeTeamSlug", "")
        away_slug = g.get("awayTeamSlug", "")
        home_abbr = SLUG_TO_ABBR.get(home_slug, home_slug.upper()[:3])
        away_abbr = SLUG_TO_ABBR.get(away_slug, away_slug.upper()[:3])

        def build(side, opp_abbr):
            w = g.get(f"{side}GoalieWins") or 0
            l = g.get(f"{side}GoalieLosses") or 0
            otl = g.get(f"{side}GoalieOvertimeLosses") or 0
            svp = g.get(f"{side}GoalieSavePercentage")
            gaa = g.get(f"{side}GoalieGoalsAgainstAvg")
            try:
                gaa_str = f"{float(gaa):.2f}" if gaa not in (None, "") else ""
            except (TypeError, ValueError):
                gaa_str = str(gaa) if gaa else ""
            try:
                svp_str = f"{float(svp):.3f}" if svp not in (None, "") else ""
            except (TypeError, ValueError):
                svp_str = str(svp) if svp else ""
            return {
                "goalie": g.get(f"{side}GoalieName") or "Unknown",
                "status": g.get(f"{side}NewsStrengthName") or "Unknown",
                "record": f"{w}-{l}-{otl}",
                "gaa": gaa_str,
                "svpct": svp_str,
                "opponent": opp_abbr,
                "home_away": "home" if side == "home" else "away",
                "news": g.get(f"{side}NewsDetails") or "",
            }

        result[home_abbr] = build("home", away_abbr)
        result[away_abbr] = build("away", home_abbr)

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--out-dir", default="data")
    ap.add_argument("--raw-html", action="store_true")
    args = ap.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("Bad date. Use YYYY-MM-DD")
        sys.exit(1)

    out = Path(args.out_dir)
    out.mkdir(exist_ok=True)

    print("Fetching DFO starting goalies...")
    html = fetch_dfo()

    if args.raw_html:
        (out / f"goalies_{args.date}.html").write_text(html, encoding="utf-8")
        print(f"Raw HTML saved: {out}/goalies_{args.date}.html")

    try:
        nd = extract_next_data(html)
        goalies = parse_goalies(nd)
    except Exception as e:
        print(f"Parse failed: {e}")
        sys.exit(2)

    out_path = out / f"goalies_{args.date}.json"
    out_path.write_text(json.dumps(goalies, indent=2), encoding="utf-8")

    print(f"\nParsed {len(goalies)} teams across {len(goalies)//2} games:\n")
    seen = set()
    for abbr, info in goalies.items():
        if abbr in seen:
            continue
        opp = info["opponent"]
        if info["home_away"] == "away":
            away, home = abbr, opp
        else:
            home, away = abbr, opp
        a = goalies[away]
        h = goalies[home]
        print(f"  {away} @ {home}")
        print(f"    {away}: {a['goalie']:<22} [{a['status']:<12}] "
              f"{a['record']:<10} {a['gaa']} / {a['svpct']}")
        print(f"    {home}: {h['goalie']:<22} [{h['status']:<12}] "
              f"{h['record']:<10} {h['gaa']} / {h['svpct']}")
        seen.add(away)
        seen.add(home)

    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
