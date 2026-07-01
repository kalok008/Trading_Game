"""
Position accounting: weighted-average pricing, realised PnL on closes
and flips, mark-to-market unrealised PnL, and settlement.

Sign convention: `quantity` on a Position is signed (positive = long,
negative = short). A fill's `signed_qty` is positive for a buy and
negative for a sell, so `apply_fill` handles opens, adds, reduces, closes,
and flip-through-zero with one code path.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    quantity: int = 0
    avg_price: float = 0.0
    realised_pnl: float = 0.0

    def unrealised_pnl(self, mark_price: float) -> float:
        return self.quantity * (mark_price - self.avg_price)

    def equity(self, mark_price: float) -> float:
        return self.realised_pnl + self.unrealised_pnl(mark_price)


def apply_fill(position: Position, signed_qty: int, price: float) -> Position:
    """Apply one fill (positive signed_qty = buy, negative = sell)."""
    if signed_qty == 0:
        return position

    same_direction = position.quantity == 0 or (position.quantity > 0) == (signed_qty > 0)

    if same_direction:
        new_quantity = position.quantity + signed_qty
        if position.quantity == 0:
            new_avg_price = price
        else:
            new_avg_price = (
                position.avg_price * abs(position.quantity) + price * abs(signed_qty)
            ) / abs(new_quantity)
        return Position(new_quantity, new_avg_price, position.realised_pnl)

    # Reducing, closing, or flipping through zero.
    direction = 1 if position.quantity > 0 else -1
    closing_qty = min(abs(signed_qty), abs(position.quantity))
    realised_delta = closing_qty * (price - position.avg_price) * direction
    new_realised = position.realised_pnl + realised_delta

    leftover = abs(signed_qty) - closing_qty
    remaining_open = position.quantity - (closing_qty * direction)

    if leftover > 0:
        # Flipped through zero: the old side is fully closed, and the
        # excess opens a brand-new position in the fill's direction.
        flip_qty = leftover if signed_qty > 0 else -leftover
        return Position(flip_qty, price, new_realised)

    new_avg_price = position.avg_price if remaining_open != 0 else 0.0
    return Position(remaining_open, new_avg_price, new_realised)


def settle(position: Position, settlement_price: float) -> Position:
    """Close a position at the final settlement price, crediting the
    remaining unrealised PnL into realised PnL and zeroing quantity."""
    if position.quantity == 0:
        return position
    realised_delta = position.quantity * (settlement_price - position.avg_price)
    return Position(0, 0.0, position.realised_pnl + realised_delta)
