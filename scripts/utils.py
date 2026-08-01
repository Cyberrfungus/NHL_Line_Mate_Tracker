"""
utils.py — Shared utility functions for the NHL Linemate Duo Tracker.
Import from any script: from scripts.utils import get_playoff_goalie_weight
"""


def derive_season_start_year(date_str: str) -> int:
    """
    Season start year for a slate date. NHL seasons run Oct–Jun, so any
    month from September onward belongs to the season starting that year;
    Jan–Aug belongs to the season that started the previous year.

    "2026-10-15" → 2026 (the 2026-27 season)
    "2027-03-01" → 2026
    """
    year, month = int(date_str[:4]), int(date_str[5:7])
    return year if month >= 9 else year - 1


def derive_season_code(date_str: str) -> str:
    """NHL API season code for a slate date, e.g. "20262027"."""
    start = derive_season_start_year(date_str)
    return f"{start}{start + 1}"


def detect_regime(date_str: str) -> str:
    """
    Auto-detect "regular" vs "playoffs" from a slate date.

    Oct–Mar is always regular season; May–Jun is always playoffs. April is
    split at the 20th (playoffs typically start Apr 18-22 — pass an explicit
    --regime flag in mid-April if the boundary lands differently that year).
    Jul–Sep (offseason/preseason) defaults to regular.
    """
    month, day = int(date_str[5:7]), int(date_str[8:10])
    if month in (5, 6):
        return "playoffs"
    if month == 4 and day >= 20:
        return "playoffs"
    return "regular"


def get_playoff_goalie_weight(game_number: int) -> float:
    """
    Return the blending weight (0.0–1.0) for playoff goalie stats.

    This weight limits recency bias for goalies. It prevents over-reacting
    to a few strong playoff games when the regular season sample (82 games)
    is much larger and more reliable.

    The returned weight is applied to playoff stats; (1 - weight) is applied
    to regular season stats when blending SV% or GSAx.

    Example:
        w = get_playoff_goalie_weight(game_number=2)
        blended_sv = w * playoff_sv + (1 - w) * season_sv

    Args:
        game_number: Number of playoff games the goalie has played in the
                     current postseason (1-based). Pass 0 for no playoff
                     games played — returns 0.0 (full season weight).

    Returns:
        float in [0.0, 0.65]
    """
    weights = {
        0: 0.00,
        1: 0.10,
        2: 0.25,
        3: 0.40,
        4: 0.55,
    }
    return weights.get(game_number, 0.65)  # game 5+ caps at 0.65


def apply_correlation_cap(
    plays: list,
    max_per_game: int = 2,
    max_per_team: int = 3,
) -> tuple[list, list]:
    """
    Limit qualified plays to at most max_per_game per game and max_per_team
    per team to prevent a single bad game script from sinking the sheet.

    Plays are ranked by composite_score descending, then stars descending
    (tiebreaker). The first play that would exceed either cap is dropped and
    recorded in the removed list.

    Args:
        plays: list of dicts, each must contain:
               - 'composite_score' (int | float)
               - 'stars'           (int, 1–5)
               - 'game_id'         (str, e.g. 'EDM@ANA')
               - 'teams'           (list[str] | str)
        max_per_game: cap per game (default 2)
        max_per_team: cap per team across all games (default 3)

    Returns:
        (selected, removed)
        selected — plays that passed the cap, in priority order
        removed  — plays dropped by the cap, each annotated with 'cap_reason'
    """
    ranked = sorted(
        plays,
        key=lambda p: (p["composite_score"], p["stars"]),
        reverse=True,
    )

    game_counts: dict[str, int] = {}
    team_counts: dict[str, int] = {}
    selected: list = []
    removed: list = []

    for play in ranked:
        game_id = play["game_id"]
        teams = play["teams"] if isinstance(play["teams"], list) else [play["teams"]]

        if game_counts.get(game_id, 0) >= max_per_game:
            removed.append({**play, "cap_reason": f"game cap ({max_per_game}/game: {game_id})"})
            continue

        capped_team = next((t for t in teams if team_counts.get(t, 0) >= max_per_team), None)
        if capped_team:
            removed.append({**play, "cap_reason": f"team cap ({max_per_team}/team: {capped_team})"})
            continue

        selected.append(play)
        game_counts[game_id] = game_counts.get(game_id, 0) + 1
        for t in teams:
            team_counts[t] = team_counts.get(t, 0) + 1

    return selected, removed

