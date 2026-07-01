# Trading_Game — Football Elo Market Trading Game

A real-time trading game: players trade shares in football teams priced by their
live probability of reaching each stage of a 16-team knockout tournament. A
pure-Python engine values every team from Elo ratings using an **exact
bracket-valuation** dynamic program, then generates skewed, never-crossing
bid/ask quotes that players trade against.

## Status

Roadmap and progress live in the [GitHub issues](https://github.com/kalok008/Trading_Game/issues)
and in [`PLAN.md`](PLAN.md).

| Phase | What it delivers | Status |
|-------|------------------|--------|
| 0 | Django + Channels bootstrap, split settings, Docker, tooling | ✅ Done |
| 1 | Core trading engine — Elo, bracket valuation, quotes, PnL (31 tests) | ✅ Done |
| 2 | Django data model — tournaments, sessions, orders, ledger | 🗓️ Next |
| 3+ | Real-time layer, execution/risk, UI, order book, quant harness, CI/deploy | ⏳ Planned |

## Stack

Django · Django Channels (ASGI / WebSockets) · Redis · PostgreSQL · vanilla JS

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows;  source .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt

python -m pytest              # 31 passing — the core trading engine
```

Local infrastructure (Postgres + Redis) is only needed from Phase 2 onward:

```bash
docker compose up -d
cp .env.example .env
```

## Layout

```
config/        Django project — split settings (base/dev/prod/test) + ASGI
gameplay/      game-session app
  services/    the trading engine (elo, bracket, valuation, quotes, pnl)
tournaments/   tournament / team / match app
accounts/      authentication
tests/         integration / unit / e2e
```

## Tests & lint

```bash
python -m pytest
ruff check .
black --check .
```
