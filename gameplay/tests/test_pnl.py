import math

from gameplay.services.pnl import Position, apply_fill, settle


def test_open_long_position():
    pos = apply_fill(Position(), signed_qty=10, price=40.0)
    assert pos.quantity == 10
    assert pos.avg_price == 40.0
    assert pos.realised_pnl == 0.0


def test_open_short_position():
    pos = apply_fill(Position(), signed_qty=-10, price=40.0)
    assert pos.quantity == -10
    assert pos.avg_price == 40.0


def test_add_to_long_position_updates_weighted_avg():
    pos = apply_fill(Position(), signed_qty=10, price=40.0)
    pos = apply_fill(pos, signed_qty=10, price=60.0)
    assert pos.quantity == 20
    assert math.isclose(pos.avg_price, 50.0)


def test_partial_close_realises_pnl_and_keeps_avg_price():
    pos = apply_fill(Position(), signed_qty=10, price=40.0)
    pos = apply_fill(pos, signed_qty=-4, price=55.0)
    assert pos.quantity == 6
    assert math.isclose(pos.avg_price, 40.0)
    assert math.isclose(pos.realised_pnl, 4 * (55.0 - 40.0))


def test_full_close_zeroes_position():
    pos = apply_fill(Position(), signed_qty=10, price=40.0)
    pos = apply_fill(pos, signed_qty=-10, price=45.0)
    assert pos.quantity == 0
    assert pos.avg_price == 0.0
    assert math.isclose(pos.realised_pnl, 10 * (45.0 - 40.0))


def test_flip_from_long_to_short_realises_pnl_on_old_side_and_opens_new():
    pos = apply_fill(Position(), signed_qty=10, price=40.0)
    pos = apply_fill(pos, signed_qty=-15, price=50.0)
    assert pos.quantity == -5
    assert pos.avg_price == 50.0
    assert math.isclose(pos.realised_pnl, 10 * (50.0 - 40.0))


def test_flip_from_short_to_long():
    pos = apply_fill(Position(), signed_qty=-10, price=40.0)
    pos = apply_fill(pos, signed_qty=15, price=30.0)
    assert pos.quantity == 5
    assert pos.avg_price == 30.0
    assert math.isclose(pos.realised_pnl, 10 * (40.0 - 30.0))


def test_unrealised_pnl_long_and_short():
    long_pos = Position(quantity=10, avg_price=40.0)
    assert math.isclose(long_pos.unrealised_pnl(50.0), 100.0)

    short_pos = Position(quantity=-10, avg_price=40.0)
    assert math.isclose(short_pos.unrealised_pnl(30.0), 100.0)


def test_settlement_closes_position_and_credits_ledger():
    pos = Position(quantity=8, avg_price=25.0)
    settled = settle(pos, settlement_price=60.0)
    assert settled.quantity == 0
    assert math.isclose(settled.realised_pnl, 8 * (60.0 - 25.0))


def test_settlement_on_flat_position_is_noop():
    pos = Position()
    assert settle(pos, 50.0) == pos
