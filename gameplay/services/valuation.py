"""
Exact bracket valuation.

Rather than Monte Carlo simulation, we compute exact terminal-outcome
probabilities for every team via dynamic programming over the knockout
tree: at each match node, combine the winner-distribution of the left
subtree with the winner-distribution of the right subtree using Elo
win probabilities, producing that node's winner-distribution and
loser-distribution. Walking the whole tree once (bottom-up) gives every
team's probability of being a Round-of-16 loss, a QF exit, fourth place,
third place, runner-up, or champion — and those probabilities are exact
given the Elo model and the current tournament state (resolved matches
short-circuit to a certainty of 1.0 for the known winner/loser).

Fair value per team is then the payout-weighted sum of those terminal
probabilities: FV_i = sum(payout[outcome] * P(team i finishes in outcome)).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .bracket import MatchNode, Node, TeamLeaf, ThirdPlaceMatch, semifinal_nodes
from .elo import win_probability

TeamDist = dict[int, float]


@dataclass
class MatchOutcome:
    winners: TeamDist = field(default_factory=dict)
    losers: TeamDist = field(default_factory=dict)


def combine_match(left: TeamDist, right: TeamDist, elo_map: dict[int, float]) -> MatchOutcome:
    """Combine two entrant distributions into a winner/loser distribution
    for the match between whoever emerges from each side."""
    winners: dict[int, float] = defaultdict(float)
    losers: dict[int, float] = defaultdict(float)

    for team_i, p_i in left.items():
        for team_j, p_j in right.items():
            matchup_prob = p_i * p_j
            if matchup_prob == 0.0:
                continue
            p_i_beats_j = win_probability(elo_map[team_i], elo_map[team_j])

            winners[team_i] += matchup_prob * p_i_beats_j
            losers[team_i] += matchup_prob * (1.0 - p_i_beats_j)

            winners[team_j] += matchup_prob * (1.0 - p_i_beats_j)
            losers[team_j] += matchup_prob * p_i_beats_j

    return MatchOutcome(dict(winners), dict(losers))


def _merge_into(target: dict[int, float], source: dict[int, float]) -> None:
    for team, prob in source.items():
        target[team] = target.get(team, 0.0) + prob


@dataclass
class BracketValuation:
    r16_loss: TeamDist
    qf_exit: TeamDist
    fourth: TeamDist
    third: TeamDist
    runner_up: TeamDist
    champion: TeamDist

    def total_probability(self, team_id: int) -> float:
        """Should be ~1.0 for every team still mathematically alive in
        the bracket — used as a correctness check in tests."""
        return (
            self.r16_loss.get(team_id, 0.0)
            + self.qf_exit.get(team_id, 0.0)
            + self.fourth.get(team_id, 0.0)
            + self.third.get(team_id, 0.0)
            + self.runner_up.get(team_id, 0.0)
            + self.champion.get(team_id, 0.0)
        )


def _winner_dist(
    node: Node, elo_map: dict[int, float], losers_by_round: dict[str, TeamDist]
) -> TeamDist:
    if isinstance(node, TeamLeaf):
        return {node.team_id: 1.0}

    if node.winner is not None:
        if node.loser is not None:
            _merge_into(losers_by_round.setdefault(node.round_name, {}), {node.loser: 1.0})
        return {node.winner: 1.0}

    left_win = _winner_dist(node.left, elo_map, losers_by_round)
    right_win = _winner_dist(node.right, elo_map, losers_by_round)
    outcome = combine_match(left_win, right_win, elo_map)
    _merge_into(losers_by_round.setdefault(node.round_name, {}), outcome.losers)
    return outcome.winners


def _third_place_dists(
    final_node: MatchNode,
    third_place: ThirdPlaceMatch,
    elo_map: dict[int, float],
    losers_by_round: dict[str, TeamDist],
) -> tuple[TeamDist, TeamDist]:
    if third_place.winner is not None and third_place.loser is not None:
        return {third_place.winner: 1.0}, {third_place.loser: 1.0}

    sf_left, sf_right = semifinal_nodes(final_node)
    # Re-derive each semifinal's loser distribution. If the semifinal is
    # already resolved this is deterministic (loser known); otherwise it
    # is the probabilistic loser distribution computed the same way as
    # every other round.
    left_loser_dist = _semifinal_loser_dist(sf_left, elo_map)
    right_loser_dist = _semifinal_loser_dist(sf_right, elo_map)
    outcome = combine_match(left_loser_dist, right_loser_dist, elo_map)
    return outcome.winners, outcome.losers


def _semifinal_loser_dist(sf_node: MatchNode, elo_map: dict[int, float]) -> TeamDist:
    if sf_node.winner is not None and sf_node.loser is not None:
        return {sf_node.loser: 1.0}
    left_win = _winner_dist(sf_node.left, elo_map, {})
    right_win = _winner_dist(sf_node.right, elo_map, {})
    return combine_match(left_win, right_win, elo_map).losers


def value_bracket(
    final_node: MatchNode, third_place: ThirdPlaceMatch, elo_map: dict[int, float]
) -> BracketValuation:
    """Walk the whole tree once and return exact terminal-outcome
    probabilities for every team, consistent with whatever subset of
    matches is already resolved on `final_node`'s subtree."""
    losers_by_round: dict[str, TeamDist] = {}
    champion_dist = _winner_dist(final_node, elo_map, losers_by_round)
    runner_up_dist = losers_by_round.get("f", {})
    r16_loss_dist = losers_by_round.get("r16", {})
    qf_exit_dist = losers_by_round.get("qf", {})

    third_dist, fourth_dist = _third_place_dists(final_node, third_place, elo_map, losers_by_round)

    return BracketValuation(
        r16_loss=r16_loss_dist,
        qf_exit=qf_exit_dist,
        fourth=fourth_dist,
        third=third_dist,
        runner_up=runner_up_dist,
        champion=champion_dist,
    )


@dataclass
class PayoutSchedule:
    r16_loss: float = 0.0
    qf_exit: float = 25.0
    fourth: float = 50.0
    third: float = 60.0
    runner_up: float = 80.0
    champion: float = 100.0


def fair_values(
    valuation: BracketValuation, payouts: PayoutSchedule, team_ids: list[int]
) -> dict[int, float]:
    """FV_i = sum over terminal outcomes of payout(outcome) * P(team i finishes there)."""
    result: dict[int, float] = {}
    for team_id in team_ids:
        result[team_id] = (
            payouts.r16_loss * valuation.r16_loss.get(team_id, 0.0)
            + payouts.qf_exit * valuation.qf_exit.get(team_id, 0.0)
            + payouts.fourth * valuation.fourth.get(team_id, 0.0)
            + payouts.third * valuation.third.get(team_id, 0.0)
            + payouts.runner_up * valuation.runner_up.get(team_id, 0.0)
            + payouts.champion * valuation.champion.get(team_id, 0.0)
        )
    return result
