"""
Fixed 16-team single-elimination knockout bracket, represented as a binary
tree of match nodes, plus a third-place match played between the two
semifinal losers.

The same tree works whether the tournament hasn't started (every match
is a probabilistic combination of Elo win probabilities) or is partway
through (some matches are resolved to a known winner/loser, and only the
remaining matches downstream stay probabilistic). This lets the exact
same valuation code produce both the pre-tournament fair value and the
live, state-aware fair value used while a game session is in progress.
"""

from __future__ import annotations

from dataclasses import dataclass

ROUND_NAMES_BY_SIZE = {16: "r16", 8: "qf", 4: "sf", 2: "f"}


@dataclass
class TeamLeaf:
    team_id: int


@dataclass
class MatchNode:
    round_name: str
    left: Node
    right: Node
    winner: int | None = None
    loser: int | None = None

    def resolve(self, winner: int) -> None:
        """Mark this match as decided. `winner` must be a team reachable
        from this node's subtree; the loser is inferred structurally by
        the caller (gameplay layer), not derived here."""
        self.winner = winner


Node = TeamLeaf | MatchNode


def build_knockout_tree(team_ids: list[int]) -> MatchNode:
    """Build the Round-of-16 -> QF -> SF -> Final tree from 16 teams in
    fixed bracket (seed) order. Adjacent pairs in `team_ids` meet in the
    Round of 16, exactly like a real single-elimination draw."""
    if len(team_ids) != 16:
        raise ValueError(f"expected exactly 16 teams, got {len(team_ids)}")

    nodes: list[Node] = [TeamLeaf(t) for t in team_ids]
    while len(nodes) > 1:
        round_name = ROUND_NAMES_BY_SIZE[len(nodes)]
        nodes = [
            MatchNode(round_name=round_name, left=nodes[i], right=nodes[i + 1])
            for i in range(0, len(nodes), 2)
        ]
    return nodes[0]


@dataclass
class ThirdPlaceMatch:
    """The extra match between the two semifinal losers. Not part of the
    binary tree because it draws its entrants from two different
    subtrees' losers rather than from a single parent match."""

    winner: int | None = None
    loser: int | None = None


def semifinal_nodes(final_node: MatchNode) -> tuple[MatchNode, MatchNode]:
    """The final's two children are, by construction, the two semifinal
    matches — their losers are the third-place match's entrants."""
    assert final_node.round_name == "f"
    left, right = final_node.left, final_node.right
    assert isinstance(left, MatchNode) and left.round_name == "sf"
    assert isinstance(right, MatchNode) and right.round_name == "sf"
    return left, right
