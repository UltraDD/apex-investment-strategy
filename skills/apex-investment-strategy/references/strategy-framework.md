# Strategy Framework

Apex Investment Strategy is a public, local-first momentum investing framework. It is intentionally smaller than any private production system: it gives users enough structure to research and build, while keeping execution decisions, data sources, and risk limits under their own control.

## Core Idea

The baseline model is cross-asset momentum:

1. Maintain a watchlist of liquid assets or fund proxies.
2. Require enough history for each asset.
3. Measure absolute and relative momentum.
4. Confirm trend with a moving average.
5. If market breadth is weak, fall back to a configured fallback asset or cash.
6. Produce target weights and let the user decide what to do.

The default public scripts are deliberately conservative in scope: one selected asset at 100% target weight, or fallback/cash when conditions fail. Users can fork the project and add risk sizing, volatility targets, multi-asset weights, costs, taxes, or execution constraints.

## Minimum History

The default configuration uses:

- `lookback_days`: 252
- `skip_recent_days`: 21
- `moving_average_days`: 160
- hard minimum: 320 effective trading days

Prefer 400-500 effective trading days before trusting current signals. Prefer 3-5 years or more for backtest interpretation.

## Public vs Private Boundaries

Public:

- Strategy structure
- Local database schema
- Research backtest scripts
- Paper wallet templates
- Local Action Packet format
- Static dashboard template

Private or user-specific:

- Broker accounts
- Real transactions
- Tax lots
- API keys
- Paid data credentials
- Personal capital allocation rules

## Good Use Cases

- "Explain how Apex-style momentum works."
- "Initialize a local strategy research workspace."
- "Validate whether my price CSV has enough history."
- "Run a simple research backtest on my data."
- "Create a paper wallet and show target drift."
- "Generate a local dashboard I can inspect."

## Bad Use Cases

- "Tell me what to buy today with my real money."
- "Connect to my broker and trade."
- "Guarantee this strategy will work."
- "Treat sample data as evidence."

