"""
Live bid/ask quote generation.

Fair value comes from the exact bracket valuation engine (`valuation.py`).
This module layers on the things that make it feel like a real dealer
market: a base spread, inventory-driven skew and widening (the dealer's
own risk management), and a small amount of noise so quotes visibly
move every tick even between bracket events. Quotes are always clamped
to [0, 100] (contracts can't be worth less than 0 or more than the
maximum payout) and never cross.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class QuoteParams:
    base_half_spread: float = 2.0
    min_half_spread: float = 0.5
    max_half_spread: float = 15.0
    inventory_skew_per_unit: float = 0.05
    inventory_widen_per_unit: float = 0.03
    noise_std: float = 0.3
    tick_size: float = 0.5
    price_floor: float = 0.0
    price_ceiling: float = 100.0


@dataclass
class Quote:
    fair_value: float
    mid: float
    bid: float
    ask: float


def _round_to_tick(price: float, tick_size: float) -> float:
    return round(price / tick_size) * tick_size


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def generate_quote(
    fair_value: float,
    dealer_inventory: int,
    params: QuoteParams | None = None,
    rng: random.Random | None = None,
) -> Quote:
    """
    `dealer_inventory` is the market-maker bot's own position for this
    team (positive = bot is net long because players have been net
    sellers to it). A long dealer skews its mid down to encourage more
    buying / discourage more selling, and widens its spread as its risk
    grows — standard inventory risk management.
    """
    params = params or QuoteParams()
    rng = rng or random.Random()

    skew = -dealer_inventory * params.inventory_skew_per_unit
    noise = rng.gauss(0.0, params.noise_std)
    mid = _clamp(fair_value + skew + noise, params.price_floor, params.price_ceiling)

    half_spread = _clamp(
        params.base_half_spread + abs(dealer_inventory) * params.inventory_widen_per_unit,
        params.min_half_spread,
        params.max_half_spread,
    )

    bid = _round_to_tick(mid - half_spread, params.tick_size)
    ask = _round_to_tick(mid + half_spread, params.tick_size)

    bid = _clamp(bid, params.price_floor, params.price_ceiling)
    ask = _clamp(ask, params.price_floor, params.price_ceiling)

    # Never cross or lock, even after clamping squeezes them together.
    if bid >= ask:
        mid_tick = _round_to_tick(mid, params.tick_size)
        bid = _clamp(
            mid_tick - params.tick_size / 2,
            params.price_floor,
            params.price_ceiling - params.tick_size,
        )
        ask = bid + params.tick_size

    return Quote(fair_value=fair_value, mid=mid, bid=bid, ask=ask)
