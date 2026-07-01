# Football Elo Market Trading Game — Execution Plan

Goal: a Django + Channels trading-game portfolio project. Stack: Django,
Channels, Redis, PostgreSQL, vanilla JS.

## Phases

| # | Phase | Status | What it delivers |
|---|-------|--------|-------------------|
| 0 | Repo, environment, Django bootstrap | **Done** | Django+Channels project, split settings (base/dev/prod/test), Docker Compose (Postgres+Redis), lint/test tooling, ASGI wiring |
| 1 | Core trading engine (pure Python) | **Done** | `elo.py`, `bracket.py`, `valuation.py` (exact DP), `quotes.py`, `pnl.py` — 31 passing tests |
| 2 | Django data model | **Next** | Tournament/Team/Match, GameSession/SessionTeamState/Order/Trade/LedgerEntry/QuoteSnapshot, admin, seed command, auth |
| 3 | Real-time layer | Pending | Consumer, session tick loop, JS socket client, play page |
| 4 | Execution, risk, settlement | Pending | Atomic dealer execution, risk checks, match resolution |
| 5 | UI | Pending | Quotes/positions/bracket/event feed, results page |
| 6 | Limit order book variant | Pending | Price-time-priority order book as an alternate market mode |
| 7 | Quant evaluation harness | Pending | Simulate thousands of sessions, report EV/variance/edge |
| 8 | Tests, CI/CD, deployment, security | Pending | GitHub Actions, hosted deploy, error monitoring, deploy checklist |

## What's built so far

`gameplay/services/`:
- `elo.py` — logistic win probability from an Elo rating difference.
- `bracket.py` — 16-team knockout tree (binary tree of match nodes) + third-place
  match; supports partial resolution (mix of known results and still-probabilistic
  future rounds) — the same structure that drives live, in-session fair value later.
- `valuation.py` — exact DP walk of the tree producing terminal-outcome
  probabilities (r16_loss/qf_exit/fourth/third/runner_up/champion) for every team,
  and payout-weighted fair value.
- `quotes.py` — bid/ask generation with inventory skew/widening and noise, never
  crossing, clamped to [0, 100].
- `pnl.py` — position accounting: opens, adds, partial closes, flip-through-zero,
  mark-to-market, and settlement.

31 unit tests, all passing, lint-clean (ruff + black).

## Next up

Phase 2: the Django models, admin, and a `seed_tournament` management command
that generates a real 16-team tournament with Elo ratings visible in the admin.
