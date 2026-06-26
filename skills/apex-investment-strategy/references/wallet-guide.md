# Wallet Guide

The public wallet layer is local and optional.

By default, create a paper wallet:

```bash
python scripts/init_wallet.py --project-dir ./my-apex --capital 100000
```

This creates wallet tables in SQLite and a `wallet/transactions.example.csv` template.

## What The Wallet Does

- Stores starting cash.
- Stores user-entered buy/sell transactions.
- Calculates approximate current holdings from local price data.
- Compares current exposure against target weights.
- Feeds the Action Packet.

## What The Wallet Does Not Do

- It does not connect to brokers.
- It does not place trades.
- It does not handle taxes or lot-level accounting.
- It does not prove that historical trades were executable.

## Transaction Fields

```csv
date,asset_id,side,quantity,price,fee,note
2026-01-02,sp500,buy,100,1.23,1.00,paper trade
```

Rules:

- `side` is `buy` or `sell`.
- `quantity`, `price`, and `fee` are non-negative numbers.
- Keep real transaction exports private unless explicitly sanitized.

