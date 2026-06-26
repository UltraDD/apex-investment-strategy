# Backtest Guide

The public backtest is a research smoke test, not a production execution simulator.

## Run

```bash
python scripts/run_backtest.py --project-dir ./my-apex
```

Outputs:

- `reports/backtest-summary.json`
- `reports/signals.csv`

## Default Signal

For each rebalance date:

1. Compute 12-1 style momentum: recent close after skipping the latest window divided by older close.
2. Require positive momentum.
3. Require price above moving average.
4. Count breadth as eligible assets divided by all configured assets with enough data.
5. If breadth is below threshold, choose fallback asset or cash.
6. Otherwise choose the eligible asset with the strongest momentum.

## Metrics

The script reports:

- CAGR
- max drawdown
- Sharpe-like annualized score from period returns
- turnover events
- final equity

These metrics are simplified. They do not include all real-world frictions by default.

## Do Not Overread

Do not describe the output as live performance. The public backtest omits many real execution effects:

- fees
- bid/ask spread
- taxes
- liquidity
- market holidays across countries
- QDII premiums or discounts
- FX
- stale or revised data
- behavior and missed execution

Use it to check that a research idea is coherent enough to inspect further.

