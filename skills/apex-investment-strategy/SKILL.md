---
name: apex-investment-strategy
description: Apex 投资策略 — public, local-first momentum investing strategy assistant. Use when a user asks to understand Apex-style momentum investing, initialize a local investment strategy workspace, build the minimum SQLite price database, validate market data coverage, run a research backtest, create a paper wallet, generate a local Action Packet, scaffold a static web dashboard, or adapt the open-source Apex investment strategy skill. This skill is research and tooling only; it must not provide personalized financial advice, touch private broker APIs, or assume access to any private Apex files, wallets, market-data warehouses, or personal workspaces.
---

# Apex 投资策略

## Overview

Apex 投资策略 helps users build a local-first, optional-layer investment strategy workspace: research notes first, then a minimum SQLite price database, then backtests, paper wallet tracking, Action Packets, and a static web dashboard when requested.

Treat every output as research infrastructure, not as personalized investment advice. Keep user data local, ask before creating persistent project files, and never connect to brokerage APIs or place trades.

## Workflow Decision Tree

| User intent | Do this first | Optional next step |
|---|---|---|
| Understand Apex / momentum investing | Read `references/strategy-framework.md` | Explain risks from `references/risk-and-disclaimer.md` |
| Build from zero | Run `scripts/init_project.py --project-dir <dir>` | Continue with database setup |
| Build a minimum database | Read `references/database-guide.md`; run `scripts/init_database.py` | Run `scripts/validate_data.py` |
| Import or validate price data | Use CSV schema in `references/database-guide.md` | Run backtest after coverage is enough |
| Run research backtest | Read `references/backtest-guide.md`; run `scripts/run_backtest.py` | Explain metrics and caveats |
| Create wallet | Read `references/wallet-guide.md`; run `scripts/init_wallet.py` | Build Action Packet |
| Generate local Action Packet | Read `references/action-packet-guide.md`; run `scripts/build_action_packet.py` | Scaffold web dashboard |
| Build frontend dashboard | Read `references/web-console-guide.md`; run `scripts/scaffold_web.py` | Open generated `web/index.html` |

## Layering Rules

- Start light. Do not create a database, wallet, or web app unless the user asks for that layer.
- Keep the baseline dependency-free: Python standard library and SQLite only.
- Use sample data only for smoke tests and UI previews. Never present sample results as market evidence.
- Treat 320 effective trading days as the hard minimum for the default momentum windows; prefer 400-500 days for signal work and 3-5 years for meaningful backtests.
- Create a paper wallet by default. Only create real-trade templates after explicit user confirmation.
- Generate Action Packets as local decision support: target weights, data health, wallet drift, and trade table. Do not auto-trade.

## Commands

Run scripts from the installed skill directory or from this repository:

```bash
python scripts/init_project.py --project-dir ./my-apex
python scripts/init_database.py --project-dir ./my-apex --sample
python scripts/validate_data.py --project-dir ./my-apex
python scripts/run_backtest.py --project-dir ./my-apex
python scripts/init_wallet.py --project-dir ./my-apex --capital 100000
python scripts/build_action_packet.py --project-dir ./my-apex
python scripts/scaffold_web.py --project-dir ./my-apex
```

On Windows PowerShell, use the same commands with `python`; all scripts use `pathlib` and avoid shell-specific behavior.

## Privacy And Safety

- Do not read or copy private local strategy files, personal wallets, real transaction logs, paid data credentials, or user-specific market-data databases unless the user explicitly points to those files for their own local use.
- Do not commit generated project data, SQLite databases, wallet files, API keys, or broker exports.
- Every generated report should include a research disclaimer.
- If the user asks for personalized buy/sell advice, redirect to explaining the generated evidence and risk caveats; do not decide for them.

## References

Use only the references needed for the current layer. Avoid loading every reference at once.
