import math

from gameplay.services.bracket import ThirdPlaceMatch, build_knockout_tree
from gameplay.services.valuation import PayoutSchedule, fair_values, value_bracket


def _equal_elo_setup(n=16, elo=1500):
    teams = list(range(1, n + 1))
    elo_map = {t: elo for t in teams}
    return teams, elo_map


def test_terminal_probabilities_sum_to_one_for_every_team():
    teams, elo_map = _equal_elo_setup()
    root = build_knockout_tree(teams)
    valuation = value_bracket(root, ThirdPlaceMatch(), elo_map)
    for t in teams:
        assert math.isclose(valuation.total_probability(t), 1.0, abs_tol=1e-9)


def test_equal_elo_bracket_is_symmetric():
    teams, elo_map = _equal_elo_setup()
    root = build_knockout_tree(teams)
    valuation = value_bracket(root, ThirdPlaceMatch(), elo_map)
    # With identical Elo for all 16 teams, every team has the same chance
    # of winning it all: 1/16.
    for t in teams:
        assert math.isclose(valuation.champion.get(t, 0.0), 1 / 16, abs_tol=1e-9)
    # And the same chance of an R16 exit: 8 losers out of 16 teams -> 0.5 each.
    for t in teams:
        assert math.isclose(valuation.r16_loss.get(t, 0.0), 0.5, abs_tol=1e-9)


def test_fair_values_are_bounded_0_to_100():
    teams, elo_map = _equal_elo_setup()
    elo_map[1] = 2200  # one very strong team
    elo_map[16] = 800  # one very weak team
    root = build_knockout_tree(teams)
    valuation = value_bracket(root, ThirdPlaceMatch(), elo_map)
    fv = fair_values(valuation, PayoutSchedule(), teams)
    for t in teams:
        assert 0.0 <= fv[t] <= 100.0


def test_strong_team_has_higher_fair_value_than_weak_team():
    teams, elo_map = _equal_elo_setup()
    elo_map[1] = 2200
    elo_map[16] = 800
    root = build_knockout_tree(teams)
    valuation = value_bracket(root, ThirdPlaceMatch(), elo_map)
    fv = fair_values(valuation, PayoutSchedule(), teams)
    assert fv[1] > fv[16]


def test_average_fair_value_matches_average_payout():
    # Sanity check: total payout mass is conserved. Average FV across all
    # teams should equal the probability-weighted average payout, which
    # for a symmetric field equals the mean of the payout schedule's
    # terminal values weighted by how many teams reach each stage
    # (8 r16 losers, 4 qf exits, 1 fourth, 1 third, 1 runner-up, 1 champion).
    teams, elo_map = _equal_elo_setup()
    root = build_knockout_tree(teams)
    valuation = value_bracket(root, ThirdPlaceMatch(), elo_map)
    payouts = PayoutSchedule()
    fv = fair_values(valuation, payouts, teams)
    total_fv = sum(fv.values())
    expected_total = (
        8 * payouts.r16_loss
        + 4 * payouts.qf_exit
        + 1 * payouts.fourth
        + 1 * payouts.third
        + 1 * payouts.runner_up
        + 1 * payouts.champion
    )
    assert math.isclose(total_fv, expected_total, rel_tol=1e-6)


def test_resolved_r16_match_collapses_uncertainty_for_that_pair():
    teams, elo_map = _equal_elo_setup()
    root = build_knockout_tree(teams)
    # Resolve the first R16 match: team 1 beats team 2.
    r16_match = root
    while r16_match.round_name != "r16":
        r16_match = r16_match.left
    r16_match.winner = 1
    r16_match.loser = 2

    valuation = value_bracket(root, ThirdPlaceMatch(), elo_map)
    assert valuation.r16_loss.get(2, 0.0) == 1.0
    assert valuation.r16_loss.get(1, 0.0) == 0.0
    # Team 1 is now guaranteed at least a QF exit; with equal Elo for
    # everyone remaining, its total probability mass should still sum to 1.
    assert math.isclose(valuation.total_probability(1), 1.0, abs_tol=1e-9)
    assert math.isclose(valuation.total_probability(2), 1.0, abs_tol=1e-9)
