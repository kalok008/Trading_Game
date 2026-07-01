"""
Elo win-probability model.

P(i beats j) uses a standard Elo logistic link:

    P(i beats j) = 1 / (1 + 10 ** (-((Ei - Ej) + h) / s))

For the MVP the tournament is played on neutral ground, so home
advantage h = 0, and the scale s = 400 (the conventional Elo default).
"""

from __future__ import annotations


def win_probability(
    elo_a: float, elo_b: float, scale: float = 400.0, home_adv: float = 0.0
) -> float:
    """Return P(team A beats team B) using a standard Elo logistic link."""
    exponent = -((elo_a - elo_b) + home_adv) / scale
    return 1.0 / (1.0 + 10.0**exponent)
