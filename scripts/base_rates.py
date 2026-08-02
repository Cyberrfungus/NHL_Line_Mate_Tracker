#!/usr/bin/env python3
"""
base_rates.py — Empirical baseline blank rates by lineup role.

Answers the question that makes every cold-stick win rate interpretable:
how often does an ORDINARY skater in a given lineup slot fail to record a
point? An 81% cold-stick hit rate is a large edge against a 68% baseline
and no edge at all against a 79% baseline. Without this number, the tier
win rates cannot be turned into a deployment decision.

Reads every date that has BOTH lineups_YYYY-MM-DD.json and
chains_YYYY-MM-DD.json in data/. Uses the same slot keys, injury
exclusions, and composite role strings as verify_players.py, so the
baselines are directly comparable to the line_role field in verified_*.json.

Usage:
    py scripts/base_rates.py
    py scripts/base_rates.py --since 2026-04-20
    py scripts/base_rates.py --since 2026-04-20 --until 2026-05-14
    py scripts/base_rates.py --csv          # machine-readable baseline table
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Mirror verify_players.py exactly so baselines are apples-to-apples
SLOT_KEYS = ["L1", "L2", "L3", "L4", "PP1", "PP2"]
INACTIVE_STATUSES = {"out", "ir", "dtd", "scratched"}

# Below this many picks, no significance verdict is offered — a perfect or
# near-perfect small record drives the normal-approximation SE toward zero
# and would otherwise report a spurious "REAL" edge.
MIN_VERDICT_OBS = 30

# Observations required before a baseline bucket is trusted for comparison.
MIN_ROLE_OBS     = 10   # exact composite role, e.g. "L3+PP2"
MIN_MARGINAL_OBS = 30   # marginal ES line or PP unit fallback


# ── loading ───────────────────────────────────────────────────────────────────

def load_json(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_dates(since=None, until=None):
    """Dates having both a lineups and a chains file, within an optional range."""
    lineup_dates = {p.stem[len("lineups_"):] for p in DATA_DIR.glob("lineups_*.json")}
    chain_dates  = {p.stem[len("chains_"):]  for p in DATA_DIR.glob("chains_*.json")}
    dates = sorted(lineup_dates & chain_dates)
    if since:
        dates = [d for d in dates if d >= since]
    if until:
        dates = [d for d in dates if d <= until]
    return dates


# ── per-date extraction ───────────────────────────────────────────────────────

def teams_that_played(chains):
    """Team abbrevs appearing in the night's game labels ('AWY@HOM')."""
    teams = set()
    for g in chains.get("games", []):
        label = g.get("label", "")
        if "@" in label:
            away, home = label.split("@", 1)
            teams.add(away.strip().upper())
            teams.add(home.strip().upper())
    return teams


def players_with_points(chains):
    """Every player appearing in any goal chain — i.e. who recorded a point."""
    scored = set()
    for goal in chains.get("goals", []):
        for player in goal.get("chain", []):
            if player:
                scored.add(player)
    return scored


def injured_names(team_data):
    """Names a team listed as out/ir/dtd/scratched — excluded, as in verify_players."""
    out = set()
    for inj in team_data.get("injuries", []):
        name = inj.get("player", "")
        if name and inj.get("status", "").lower() in INACTIVE_STATUSES:
            out.add(name)
    for name in team_data.get("scratched", []):
        if name:
            out.add(name)
    return out


def composite_role(roles):
    """Build the same 'L2+PP1' role string verify_players writes to cold_sticks."""
    es = sorted(r for r in roles if r.startswith("L"))
    pp = sorted(r for r in roles if r.startswith("PP"))
    return "+".join(es + pp)


def date_observations(lineups, chains):
    """
    Yield one observation per dressed skater in a slot on a playing team:
        {name, team, roles, role_key, es_line, on_pp, blanked}
    """
    playing = teams_that_played(chains)
    scored  = players_with_points(chains)

    for team, td in lineups.items():
        if team not in playing:
            continue
        if not isinstance(td, dict) or "error" in td or "L1" not in td:
            continue

        hurt = injured_names(td)
        roles_by_player = defaultdict(list)
        for key in SLOT_KEYS:
            for name in td.get(key, []):
                if not name or name in hurt:
                    continue
                if key not in roles_by_player[name]:
                    roles_by_player[name].append(key)

        for name, roles in roles_by_player.items():
            es = next((r for r in roles if r.startswith("L")), None)
            pp = next((r for r in roles if r.startswith("PP")), None)
            yield {
                "name":     name,
                "team":     team,
                "roles":    roles,
                "role_key": composite_role(roles),
                "es_line":  es,
                "on_pp":    pp,
                "blanked":  name not in scored,
            }


# ── aggregation ───────────────────────────────────────────────────────────────

class Rate:
    __slots__ = ("blank", "total")

    def __init__(self):
        self.blank = 0
        self.total = 0

    def add(self, blanked):
        self.total += 1
        self.blank += 1 if blanked else 0

    @property
    def pct(self):
        return 0.0 if self.total == 0 else 100.0 * self.blank / self.total

    @property
    def stderr(self):
        """Standard error of the blank rate, in percentage points."""
        if self.total == 0:
            return 0.0
        p = self.blank / self.total
        return 100.0 * (p * (1 - p) / self.total) ** 0.5


def bar(p, width=20):
    filled = int(round(p / 100 * width))
    return "█" * filled + "░" * (width - filled)


def rate_row(label, r, width=26):
    return (f"  {label:<{width}}  {r.blank:4d}/{r.total:4d}  "
            f"{r.pct:5.1f}%  ±{r.stderr:4.1f}  {bar(r.pct)}")


def section(title):
    print(f"\n{'─' * 68}")
    print(f"  {title}")
    print(f"{'─' * 68}")


# ── cold stick edge vs baseline ───────────────────────────────────────────────

def role_baseline(role_key, by_role, by_es, by_pp, overall, sources):
    """
    Best available baseline for a role string, most specific first:
      exact composite role -> even-strength line -> PP unit -> all slots.
    Falling straight to the all-slots average would compare an L4 grinder
    against a pool that includes L1 scorers, so the marginal ES-line rate
    (always in the hundreds of observations) is used before that.
    """
    parts = role_key.split("+") if role_key else []

    r = by_role.get(role_key)
    if r and r.total >= MIN_ROLE_OBS:
        sources["exact role"] += 1
        return r.pct

    es = next((p for p in parts if p.startswith("L")), None)
    if es and by_es[es].total >= MIN_MARGINAL_OBS:
        sources["ES line"] += 1
        return by_es[es].pct

    pp = next((p for p in parts if p.startswith("PP")), None)
    if pp and by_pp[pp].total >= MIN_MARGINAL_OBS:
        sources["PP unit"] += 1
        return by_pp[pp].pct

    sources["all slots"] += 1
    return overall.pct


def roles_from_lineups(lineups):
    """player -> composite role string, for filling in picks missing line_role."""
    out = {}
    for team, td in (lineups or {}).items():
        if not isinstance(td, dict) or "L1" not in td:
            continue
        roles = defaultdict(list)
        for key in SLOT_KEYS:
            for name in td.get(key, []):
                if name and key not in roles[name]:
                    roles[name].append(key)
        for name, rl in roles.items():
            out[name] = composite_role(rl)
    return out


def role_class(role_key):
    """
    HIGH  — occupies L1, L2, or PP1: a scoring role the market prices near
            even money, so a cold read there is worth real money.
    DEPTH — L3/L4/PP2 only: already expected to blank, and priced accordingly.
    Matches the high_role flag verify_players writes to cold_sticks.
    """
    parts = role_key.split("+") if role_key else []
    return "HIGH" if any(p in ("L1", "L2", "PP1") for p in parts) else "DEPTH"


def implied_american(pct):
    """Fair American odds for a probability given in percent."""
    if pct <= 0 or pct >= 100:
        return "—"
    if pct >= 50:
        return f"{-round(pct / (100 - pct) * 100):d}"
    return f"+{round((100 - pct) / pct * 100):d}"


def cold_stick_edge(dates, by_role, by_es, by_pp, overall):
    """
    Score cold sticks straight from verified + chains (same rule as
    score_results: a cold stick WINS if the player recorded no point),
    and attach the baseline for that pick's exact lineup role.

    Returns (picks, sources); picks is one record per cold-stick pick so the
    reporting layer can slice by tier, role, or role class without rescanning.
    """
    picks   = []
    sources = defaultdict(int)   # which baseline granularity was used

    for d in dates:
        verified = load_json(DATA_DIR / f"verified_{d}.json")
        chains   = load_json(DATA_DIR / f"chains_{d}.json")
        if not verified or not chains:
            continue
        scored = players_with_points(chains)
        derived = None   # lazily built only if a pick is missing line_role

        for cs in verified.get("cold_sticks", []):
            role = cs.get("line_role", "") or ""
            if role in ("", "?"):
                if derived is None:
                    derived = roles_from_lineups(load_json(DATA_DIR / f"lineups_{d}.json"))
                role = derived.get(cs["name"], "")

            picks.append({
                "date":       d,
                "name":       cs["name"],
                "tier":       cs.get("tier", "?"),
                "role":       role or "(unknown)",
                "role_class": role_class(role),
                "won":        cs["name"] not in scored,
                "baseline":   role_baseline(role, by_role, by_es, by_pp,
                                            overall, sources),
            })

    return picks, sources


def summarize(picks):
    """(wins, total, observed_pct, baseline_pct, edge_pts, stderr_pts)."""
    total = len(picks)
    if not total:
        return 0, 0, 0.0, 0.0, 0.0, 0.0
    wins     = sum(1 for p in picks if p["won"])
    obs      = 100.0 * wins / total
    baseline = sum(p["baseline"] for p in picks) / total
    se       = 100.0 * ((obs / 100) * (1 - obs / 100) / total) ** 0.5
    return wins, total, obs, baseline, obs - baseline, se


def verdict_for(edge, se, total):
    """Significance label, gated on sample size to avoid a spurious 'REAL'."""
    if total < MIN_VERDICT_OBS:
        return f"thin sample (n<{MIN_VERDICT_OBS})"
    if edge > 2 * se:
        return "REAL (>2 SE)"
    if edge > se:
        return "weak (1-2 SE)"
    if edge > 0:
        return "noise (<1 SE)"
    return "NO EDGE"


# ── duo correlation decomposition ─────────────────────────────────────────────

def duo_decomposition(dates):
    """
    P(both players of a duo record a point) and P(they share a goal chain |
    both recorded a point). The second number is the correlation the duo
    signal is actually built on.
    """
    try:
        from score_results import build_chain_lookup, get_lineup_aware_pairs
    except ImportError:
        return None

    stats = defaultdict(lambda: {"pairs": 0, "both": 0, "chained": 0})

    for d in dates:
        verified = load_json(DATA_DIR / f"verified_{d}.json")
        chains   = load_json(DATA_DIR / f"chains_{d}.json")
        lineups  = load_json(DATA_DIR / f"lineups_{d}.json")
        if not verified or not chains:
            continue

        active, pair_map = build_chain_lookup(chains)
        hot_by_team = defaultdict(list)
        for p in verified.get("hot_players", []):
            hot_by_team[p["team"]].append(p["name"])

        for p1, p2, _team, tier in get_lineup_aware_pairs(lineups, hot_by_team):
            s = stats[tier]
            s["pairs"] += 1
            both = p1 in active and p2 in active
            if both:
                s["both"] += 1
            if frozenset({p1, p2}) in pair_map:
                s["chained"] += 1
    return stats


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Empirical blank-rate baselines by lineup role")
    ap.add_argument("--since", default=None, help="Start date, inclusive (YYYY-MM-DD)")
    ap.add_argument("--until", default=None, help="End date, inclusive (YYYY-MM-DD)")
    ap.add_argument("--csv", action="store_true", help="Emit the role baseline table as CSV")
    ap.add_argument("--min-obs", type=int, default=10,
                    help="Minimum observations to display a role bucket (default: 10)")
    args = ap.parse_args()

    dates = find_dates(args.since, args.until)
    if not dates:
        print("No dates found with BOTH lineups_*.json and chains_*.json in data/.")
        print("Run fetch_postgame.py chains --date YYYY-MM-DD to generate chain files.")
        sys.exit(1)

    overall    = Rate()
    by_es      = defaultdict(Rate)
    by_pp      = defaultdict(Rate)
    by_role    = defaultdict(Rate)
    games      = 0
    goals      = 0

    for d in dates:
        lineups = load_json(DATA_DIR / f"lineups_{d}.json")
        chains  = load_json(DATA_DIR / f"chains_{d}.json")
        if not lineups or not chains:
            continue
        games += chains.get("games_count", 0)
        goals += chains.get("goals_count", 0)

        for obs in date_observations(lineups, chains):
            overall.add(obs["blanked"])
            if obs["es_line"]:
                by_es[obs["es_line"]].add(obs["blanked"])
            by_pp["PP1" if obs["on_pp"] == "PP1" else
                  "PP2" if obs["on_pp"] == "PP2" else "no PP"].add(obs["blanked"])
            by_role[obs["role_key"]].add(obs["blanked"])

    if args.csv:
        w = csv.writer(sys.stdout)
        w.writerow(["role", "blanked", "total", "blank_pct", "stderr_pts"])
        for role in sorted(by_role, key=lambda r: -by_role[r].total):
            r = by_role[role]
            w.writerow([role, r.blank, r.total, f"{r.pct:.1f}", f"{r.stderr:.1f}"])
        return

    print(f"\n{'=' * 68}")
    print(f"  BASELINE BLANK RATES  ({dates[0]} → {dates[-1]})")
    print(f"{'=' * 68}")
    print(f"  {len(dates)} dates | {games} games | {goals} goals | "
          f"{overall.total} skater-games observed")
    print(f"  'Blank' = player dressed in an L1-L4/PP slot and recorded no point.")

    section("BASELINE — by even-strength line")
    for line in ("L1", "L2", "L3", "L4"):
        if by_es[line].total >= args.min_obs:
            print(rate_row(line, by_es[line]))

    section("BASELINE — by power-play unit")
    for unit in ("PP1", "PP2", "no PP"):
        if by_pp[unit].total >= args.min_obs:
            print(rate_row(unit, by_pp[unit]))

    section(f"BASELINE — by composite role (n >= {args.min_obs})")
    for role in sorted(by_role, key=lambda r: -by_role[r].total):
        if by_role[role].total >= args.min_obs:
            print(rate_row(role or "(none)", by_role[role]))

    section("BASELINE — all dressed skaters")
    print(rate_row("ALL SLOTS", overall))

    # ── the decisive comparison ───────────────────────────────────────────────
    picks, sources = cold_stick_edge(dates, by_role, by_es, by_pp, overall)
    if picks:
        def edge_row(label, group, width=16):
            wins, total, obs, base, edge, se = summarize(group)
            if not total:
                return
            print(f"  {label:<{width}} {wins:4d}/{total:<4d} {obs:5.1f}%  "
                  f"{base:8.1f}%  {edge:+7.1f}pt  {verdict_for(edge, se, total)}")

        section("COLD STICKS vs BASELINE  ← the number that matters")
        print(f"  {'Tier':<16} {'Observed':>10}  {'Baseline':>9}  {'Edge':>8}  Verdict")
        print(f"  {'-'*16} {'-'*10}  {'-'*9}  {'-'*8}  {'-'*24}")
        for tier in sorted({p["tier"] for p in picks}):
            edge_row(f"Tier {tier}", [p for p in picks if p["tier"] == tier])
        print(f"\n  Edge = how much better the tier does than an ordinary skater")
        print(f"  in the SAME lineup role. SE on the observed rate is the yardstick;")
        print(f"  an edge inside 1 SE is indistinguishable from picking at random.")

        total_src = sum(sources.values()) or 1
        print(f"\n  Baseline granularity used (more specific = more trustworthy):")
        for src in ("exact role", "ES line", "PP unit", "all slots"):
            if sources.get(src):
                n = sources[src]
                print(f"    {src:<12} {n:4d}  ({100 * n // total_src:3d}%)")
        if sources.get("all slots"):
            print(f"    ^ 'all slots' compares a pick against the league-wide average")
            print(f"      rather than its own role — treat those as approximate.")

        # ── where the edge actually lives ─────────────────────────────────────
        section("COLD STICKS BY ROLE CLASS  ← where the edge is worth money")
        print(f"  HIGH  = pick occupies L1, L2, or PP1   (market prices these near even)")
        print(f"  DEPTH = L3/L4/PP2 only                 (already expected to blank)\n")
        print(f"  {'Group':<16} {'Observed':>10}  {'Baseline':>9}  {'Edge':>8}  Verdict")
        print(f"  {'-'*16} {'-'*10}  {'-'*9}  {'-'*8}  {'-'*24}")
        for tier in sorted({p["tier"] for p in picks}):
            for cls in ("HIGH", "DEPTH"):
                edge_row(f"Tier {tier} / {cls}",
                         [p for p in picks
                          if p["tier"] == tier and p["role_class"] == cls])
        print()
        for cls in ("HIGH", "DEPTH"):
            edge_row(f"ALL {cls}", [p for p in picks if p["role_class"] == cls])

        print(f"\n  {'Group':<16} {'Baseline price':>15} {'Observed price':>15}")
        print(f"  {'-'*16} {'-'*15} {'-'*15}")
        for cls in ("HIGH", "DEPTH"):
            grp = [p for p in picks if p["role_class"] == cls]
            if not grp:
                continue
            _, _, obs, base, _, _ = summarize(grp)
            print(f"  {'ALL ' + cls:<16} {implied_american(base):>15} "
                  f"{implied_american(obs):>15}")
        print(f"\n  Baseline price is roughly what an under-0.5-points line should")
        print(f"  cost for an ordinary player in that role; observed price is what")
        print(f"  your picks actually earned. The gap between them is the edge, and")
        print(f"  it is only bankable if the market is not already charging for it.")

        section("COLD STICK ROLE MIX  (what roles the picks actually occupy)")
        for tier in sorted({p["tier"] for p in picks}):
            tier_picks = [p for p in picks if p["tier"] == tier]
            counts = defaultdict(int)
            for p in tier_picks:
                counts[p["role"]] += 1
            print(f"  Tier {tier}  (n={len(tier_picks)})")
            for role, n in sorted(counts.items(), key=lambda kv: -kv[1])[:6]:
                base = by_role.get(role)
                base_str = f"{base.pct:5.1f}%" if base and base.total >= MIN_ROLE_OBS else "   n/a"
                print(f"    {role:<14} {n:4d} picks   [{role_class(role):<5}]"
                      f"   role baseline {base_str}")

    # ── duo correlation ───────────────────────────────────────────────────────
    duos = duo_decomposition(dates)
    if duos:
        section("HOT DUOS — correlation decomposition")
        print(f"  {'Tier':<12} {'pairs':>6} {'P(both pts)':>12} {'P(chain|both)':>14} {'P(chain)':>9}")
        print(f"  {'-'*12} {'-'*6} {'-'*12} {'-'*14} {'-'*9}")
        for tier in sorted(duos, key=lambda t: -duos[t]["pairs"]):
            s = duos[tier]
            if not s["pairs"]:
                continue
            p_both  = 100.0 * s["both"] / s["pairs"]
            p_cond  = 100.0 * s["chained"] / s["both"] if s["both"] else 0.0
            p_chain = 100.0 * s["chained"] / s["pairs"]
            print(f"  {tier:<12} {s['pairs']:6d} {p_both:11.1f}% "
                  f"{p_cond:13.1f}% {p_chain:8.1f}%")
        print(f"\n  P(both pts)   — both duo players recorded a point (the SGP leg)")
        print(f"  P(chain|both) — given both scored, they shared a goal. This is the")
        print(f"                  correlation the duo thesis rests on; >50% means the")
        print(f"                  legs are genuinely linked, not independent events.")

    print()


if __name__ == "__main__":
    main()
