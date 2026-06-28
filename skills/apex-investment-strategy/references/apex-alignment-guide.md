# Apex Alignment Guide

This guide helps a user move from the public demo workflow toward an Apex-like research system without copying private production data, credentials, wallets, broker state, or personal trading rules.

The goal is alignment in shape, not identity. The public repository provides a local-first research framework that can grow toward a 17-asset Apex-style workflow; it is not a managed strategy service and does not ship live market data.

## When To Use This Guide

Use this guide when the user asks for:

- a setup closer to the full Apex system
- a 17-asset universe instead of the minimal demo
- an explanation of how to add tournament selection, volatility sizing, or risk-defense rules
- a migration path from sample data to their own local price data

Do not use this guide to infer personalized buy/sell advice. Keep every output research-only.

## Start With The Apex-Aligned Profile

Initialize the workspace with the public 17-asset profile:

```bash
python scripts/init_project.py --project-dir ./my-apex --profile apex17
```

Then inspect `config.json`. The profile includes 17 non-cash assets:

```text
hs300, sse50, csi500, csi_div, chinext, bse50, consumer, healthcare,
financials, infotech, military, newenergy, realestate, semiconductor,
nonferrous, sp500, nasdaq100
```

The default scripts will still run the simple public baseline: 12-1 style momentum, moving-average confirmation, breadth check, then one selected asset or fallback/cash. That is intentional. It gives the user a runnable starting point before they add more advanced layers.

## Data Contract

Ask the user to provide local price data before treating any signal as evidence.

Required CSV columns:

```csv
date,asset_id,close
```

Optional:

```csv
volume
```

Rules:

- Every `asset_id` must match `config.json`.
- Use consistent adjusted or unadjusted close prices across all assets.
- Each asset needs at least 320 effective trading days; prefer 400-500 days for current signals and 3-5 years for research backtests.
- Sample data is only for smoke tests and UI previews.
- Keep raw data, credentials, and broker exports local.

Import and validate:

```bash
python scripts/init_database.py --project-dir ./my-apex --csv ./prices.csv
python scripts/validate_data.py --project-dir ./my-apex
```

## Alignment Roadmap

Work in this order. Do not jump to a polished dashboard before the data and signal layers are trustworthy.

1. Universe and data health

Confirm the 17 assets, local data coverage, missing days, stale rows, adjusted-price policy, and source notes. The Action Packet should surface data health before targets.

2. Momentum baseline

Keep the public 12-1 momentum baseline working first:

- `lookback_days`: 252
- `skip_recent_days`: 21
- moving-average filter
- breadth gate
- fallback asset or cash

3. Tournament selection

Add a separate research module before replacing the baseline. A public tournament layer should document:

- candidate assets after data and trend filters
- the comparison statistic used
- the minimum sample size
- the threshold for declaring one asset meaningfully ahead
- what happens when the winner is not statistically clear

Avoid pretending the threshold is universal. Users should choose and test it against their own data.

4. Volatility position sizing

Add position sizing after selection is stable. A public version should expose:

- realized-volatility window
- target volatility
- max exposure
- min trade value
- no-trade zone
- fallback behavior when volatility data is missing

Make the Action Packet show both raw target weight and clipped final weight.

5. Risk-defense gates

Add defense rules as explicit gates, not hidden overrides. Common public-safe gates include:

- breadth weakness
- price below moving average
- high realized volatility
- severe drawdown state
- missing or stale data
- execution calendar mismatch

When a defense gate changes the target, record the reason in the Action Packet.

6. Execution mapping

Keep strategy assets separate from executable instruments. If users map indexes to ETFs or funds, store that mapping locally and show it as an assumption, not as broker integration.

7. Action Packet maturity

A mature local Action Packet should include:

- signal date
- data health
- candidate ranking
- tournament result
- risk gates
- target weights before and after risk sizing
- paper wallet drift
- possible paper trades
- research disclaimer

## Suggested Codex Prompt For Users

```text
Use the Apex Alignment Guide. Initialize an Apex-aligned 17-asset local workspace, inspect the generated config, then help me import my local price CSV. Do not give trading advice. First validate data coverage and only then run the public baseline backtest and Action Packet.
```

## Definition Of Close Enough

The user's local system is close to the Apex shape when all of these are true:

- `config.json` has the 17-asset public universe or a documented user-specific variant.
- Every asset has enough local history and a known data source.
- The baseline signal runs and produces reproducible outputs.
- Advanced tournament, volatility, and defense layers are documented and tested before being trusted.
- Action Packets explain why a target changed.
- Sample data is never cited as market evidence.
- No private broker, wallet, credential, or paid-source state is committed.

