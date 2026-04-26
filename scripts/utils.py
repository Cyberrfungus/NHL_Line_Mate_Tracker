"""
utils.py — Shared utility functions for the NHL Linemate Duo Tracker.
Import from any script: from scripts.utils import get_playoff_goalie_weight
"""


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
