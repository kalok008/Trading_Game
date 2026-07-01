import math

from gameplay.services.elo import win_probability


def test_probabilities_sum_to_one():
    p = win_probability(1600, 1500)
    q = win_probability(1500, 1600)
    assert math.isclose(p + q, 1.0, abs_tol=1e-9)


def test_equal_elo_is_half():
    assert math.isclose(win_probability(1500, 1500), 0.5, abs_tol=1e-9)


def test_higher_elo_favoured():
    assert win_probability(1700, 1500) > 0.5
    assert win_probability(1300, 1500) < 0.5


def test_probability_in_unit_interval():
    for diff in [-1000, -400, 0, 400, 1000]:
        p = win_probability(1500 + diff, 1500)
        assert 0.0 < p < 1.0
