import random

from gameplay.services.quotes import QuoteParams, generate_quote


def test_quotes_never_cross():
    rng = random.Random(42)
    for _ in range(1000):
        fv = rng.uniform(0, 100)
        inv = rng.randint(-200, 200)
        q = generate_quote(fv, inv, rng=rng)
        assert q.bid < q.ask


def test_quotes_stay_within_bounds():
    rng = random.Random(7)
    for _ in range(500):
        fv = rng.uniform(0, 100)
        inv = rng.randint(-500, 500)
        q = generate_quote(fv, inv, rng=rng)
        assert 0.0 <= q.bid <= 100.0
        assert 0.0 <= q.ask <= 100.0


def test_extreme_fair_value_still_bounded():
    q_low = generate_quote(0.5, 0, rng=random.Random(1))
    q_high = generate_quote(99.5, 0, rng=random.Random(1))
    assert q_low.bid >= 0.0
    assert q_high.ask <= 100.0


def test_long_dealer_inventory_skews_mid_down():
    params = QuoteParams(noise_std=0.0)  # isolate the skew effect
    flat = generate_quote(50.0, 0, params, rng=random.Random(0))
    dealer_long = generate_quote(50.0, 100, params, rng=random.Random(0))
    assert dealer_long.mid < flat.mid


def test_short_dealer_inventory_skews_mid_up():
    params = QuoteParams(noise_std=0.0)
    flat = generate_quote(50.0, 0, params, rng=random.Random(0))
    dealer_short = generate_quote(50.0, -100, params, rng=random.Random(0))
    assert dealer_short.mid > flat.mid


def test_larger_inventory_widens_spread():
    params = QuoteParams(noise_std=0.0)
    tight = generate_quote(50.0, 0, params, rng=random.Random(0))
    wide = generate_quote(50.0, 300, params, rng=random.Random(0))
    assert (wide.ask - wide.bid) > (tight.ask - tight.bid)
