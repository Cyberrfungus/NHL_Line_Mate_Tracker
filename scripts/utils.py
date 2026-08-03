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


# NOTE: apply_correlation_cap() lived here from Apr 25 – Aug 1 2026 and was
# never called by any pipeline step. It ranked on a `composite_score` field
# that nothing in the pipeline ever populated, so it could not have run
# correctly if wired up. The correlation cap is applied by hand in the play
# sheet — see prompts/nightly_play_sheet_v6.md § 6.5 and CORRELATION CAP in
# .claude/STATE.md. Removed rather than left looking live.

