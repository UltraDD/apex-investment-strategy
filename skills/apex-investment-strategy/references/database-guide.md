# Database Guide

The public baseline uses SQLite because it ships with Python and keeps data local.

## Create The Database

```bash
python scripts/init_project.py --project-dir ./my-apex
python scripts/init_database.py --project-dir ./my-apex
```

For a smoke test with deterministic sample data:

```bash
python scripts/init_database.py --project-dir ./my-apex --sample
```

If the workspace was initialized with `--profile apex17`, the same CSV rules apply. Provide rows for all 17 configured asset ids before treating validation or backtest output as market evidence.

## CSV Schema

Required columns:

```csv
date,asset_id,close
```

Optional columns:

```csv
volume
```

Rules:

- `date` must be ISO `YYYY-MM-DD`.
- `asset_id` must match an asset id in `config.json`.
- `close` must be positive.
- Duplicate `(asset_id, date)` rows are replaced.
- Keep source files local unless the user explicitly wants to publish a sanitized example.

## SQLite Tables

`price_daily`

| Column | Type | Meaning |
|---|---|---|
| asset_id | TEXT | Asset id from config |
| date | TEXT | ISO date |
| close | REAL | Closing price or adjusted close, chosen consistently |
| volume | REAL | Optional volume |

`wallet_transactions`

Stores paper wallet or user-entered transactions.

`wallet_settings`

Stores local wallet settings such as starting cash.

## Validation

```bash
python scripts/validate_data.py --project-dir ./my-apex
```

The validator checks:

- required tables
- assets in config
- row counts by asset
- earliest and latest date by asset
- whether each asset meets `min_history_days`

It does not certify data correctness. Users still need to verify splits, dividends, adjusted vs unadjusted prices, time zones, stale rows, and missing days.
