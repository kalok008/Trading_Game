import pytest

from gameplay.services.bracket import build_knockout_tree, semifinal_nodes


def _teams():
    return list(range(1, 17))


def test_tree_has_16_leaves_and_correct_rounds():
    root = build_knockout_tree(_teams())
    assert root.round_name == "f"

    left_sf, right_sf = semifinal_nodes(root)
    assert left_sf.round_name == "sf"
    assert right_sf.round_name == "sf"

    for qf_node in (left_sf.left, left_sf.right, right_sf.left, right_sf.right):
        assert qf_node.round_name == "qf"


def test_rejects_wrong_team_count():
    with pytest.raises(ValueError):
        build_knockout_tree(list(range(1, 9)))
