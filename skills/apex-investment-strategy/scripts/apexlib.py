from __future__ import annotations

import argparse
import bisect
import copy
import csv
import datetime as dt
import json
import math
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


DISCLAIMER = (
    "本地研究输出，仅用于研究，不构成个性化投资建议、实盘表现或交易指令。"
)

AI_SYSTEM_PROMPT = (
    "You are the AI research interpretation layer inside a local momentum research tool. "
    "Explain only the provided local research outputs. Do not provide personalized financial advice, "
    "do not tell the user to buy or sell, do not promise returns, and do not invent missing data."
)
DEFAULT_AI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_AI_MODEL = "gpt-4.1-mini"

DEFAULT_CONFIG: dict[str, Any] = {
    "schema_version": 1,
    "currency": "CNY",
    "strategy": {
        "lookback_days": 252,
        "skip_recent_days": 21,
        "moving_average_days": 160,
        "breadth_min_ratio": 0.33,
        "fallback_asset": "sp500",
        "min_history_days": 320,
        "min_trade_value": 100.0,
    },
    "assets": [
        {"id": "sp500", "name": "S&P 500 proxy", "group": "external_equity"},
        {"id": "nasdaq100", "name": "Nasdaq 100 proxy", "group": "external_equity"},
        {"id": "hs300", "name": "CSI 300 proxy", "group": "china_broad"},
        {"id": "csi500", "name": "CSI 500 proxy", "group": "china_broad"},
        {"id": "cash", "name": "Cash reserve", "group": "cash"},
    ],
}

APEX_ALIGNED_17_CONFIG: dict[str, Any] = {
    "schema_version": 1,
    "profile": "apex17",
    "currency": "CNY",
    "strategy": {
        "lookback_days": 252,
        "skip_recent_days": 21,
        "moving_average_days": 160,
        "breadth_min_ratio": 0.33,
        "fallback_asset": "sp500",
        "min_history_days": 320,
        "min_trade_value": 100.0,
        "selection_mode": "single_winner_public_baseline",
        "next_extensions": [
            "significance_tournament",
            "volatility_position_sizing",
            "risk_defense_gates",
            "execution_calendar_mapping",
        ],
    },
    "assets": [
        {"id": "hs300", "name": "CSI 300 proxy", "group": "china_broad"},
        {"id": "sse50", "name": "SSE 50 proxy", "group": "china_broad"},
        {"id": "csi500", "name": "CSI 500 proxy", "group": "china_broad"},
        {"id": "csi_div", "name": "CSI dividend proxy", "group": "china_style"},
        {"id": "chinext", "name": "ChiNext proxy", "group": "china_growth"},
        {"id": "bse50", "name": "BSE 50 proxy", "group": "china_growth"},
        {"id": "consumer", "name": "China consumer proxy", "group": "china_sector"},
        {"id": "healthcare", "name": "China healthcare proxy", "group": "china_sector"},
        {"id": "financials", "name": "China financials proxy", "group": "china_sector"},
        {"id": "infotech", "name": "China information technology proxy", "group": "china_sector"},
        {"id": "military", "name": "China military industry proxy", "group": "china_sector"},
        {"id": "newenergy", "name": "China new energy proxy", "group": "china_sector"},
        {"id": "realestate", "name": "China real estate proxy", "group": "china_sector"},
        {"id": "semiconductor", "name": "China semiconductor proxy", "group": "china_sector"},
        {"id": "nonferrous", "name": "China non-ferrous metals proxy", "group": "china_sector"},
        {"id": "sp500", "name": "S&P 500 proxy", "group": "external_equity"},
        {"id": "nasdaq100", "name": "Nasdaq 100 proxy", "group": "external_equity"},
        {"id": "cash", "name": "Cash reserve", "group": "cash"},
    ],
    "alignment_notes": [
        "This public profile is a privacy-safe starting point for an Apex-like 17-asset workspace.",
        "It does not include private production data, broker state, paid credentials, or personalized trading rules.",
        "Use the alignment guide before adding tournament, volatility sizing, or risk-defense behavior.",
    ],
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS price_daily (
    asset_id TEXT NOT NULL,
    date TEXT NOT NULL,
    close REAL NOT NULL,
    volume REAL,
    PRIMARY KEY (asset_id, date)
);

CREATE TABLE IF NOT EXISTS wallet_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wallet_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity REAL NOT NULL CHECK (quantity >= 0),
    price REAL NOT NULL CHECK (price >= 0),
    fee REAL NOT NULL DEFAULT 0 CHECK (fee >= 0),
    note TEXT
);
"""


@dataclass(frozen=True)
class PricePoint:
    date: str
    close: float
    volume: float | None = None


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def project_root(project_dir: str | Path) -> Path:
    return Path(project_dir).expanduser().resolve()


def config_path(project_dir: str | Path) -> Path:
    return project_root(project_dir) / "config.json"


def db_path(project_dir: str | Path) -> Path:
    return project_root(project_dir) / "data" / "apex.sqlite"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config(project_dir: str | Path) -> dict[str, Any]:
    path = config_path(project_dir)
    if not path.exists():
        raise ValueError(f"Missing config.json. Run init_project.py first: {path}")
    return read_json(path)


def asset_ids(config: dict[str, Any], include_cash: bool = False) -> list[str]:
    ids = [asset["id"] for asset in config.get("assets", [])]
    if include_cash:
        return ids
    return [asset_id for asset_id in ids if asset_id != "cash"]


def profile_config(profile: str = "minimal") -> dict[str, Any]:
    normalized = profile.strip().lower()
    if normalized in {"minimal", "default"}:
        return copy.deepcopy(DEFAULT_CONFIG)
    if normalized in {"apex17", "apex-aligned-17"}:
        return copy.deepcopy(APEX_ALIGNED_17_CONFIG)
    raise ValueError("Unknown profile. Use 'minimal' or 'apex17'.")


def ensure_project(project_dir: str | Path, overwrite: bool = False, profile: str = "minimal") -> Path:
    root = project_root(project_dir)
    root.mkdir(parents=True, exist_ok=True)
    for dirname in ("data", "reports", "wallet", "web", "logs"):
        (root / dirname).mkdir(exist_ok=True)

    cfg = config_path(root)
    if overwrite or not cfg.exists():
        write_json(cfg, profile_config(profile))

    readme = root / "README.md"
    if overwrite or not readme.exists():
        profile_line = (
            "This workspace uses the public Apex-aligned 17-asset profile.\n\n"
            if profile.strip().lower() in {"apex17", "apex-aligned-17"}
            else ""
        )
        readme.write_text(
            "# Local Apex Investment Strategy Workspace\n\n"
            f"{profile_line}"
            "This workspace is local and research-only. Generated data, wallet files, "
            "and reports should stay private unless you intentionally sanitize and publish them.\n\n"
            "Typical flow:\n\n"
            "1. Import or generate price data.\n"
            "2. Validate coverage.\n"
            "3. Run a research backtest.\n"
            "4. Initialize a paper wallet.\n"
            "5. Build an Action Packet.\n"
            "6. Generate the static web dashboard.\n",
            encoding="utf-8",
        )

    ignore = root / ".gitignore"
    if overwrite or not ignore.exists():
        ignore.write_text(
            "data/*.sqlite\n"
            "reports/*.json\n"
            "reports/*.csv\n"
            "wallet/*.csv\n"
            "web/index.html\n"
            ".env\n",
            encoding="utf-8",
        )
    return root


def connect(project_dir: str | Path) -> sqlite3.Connection:
    path = db_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    return conn


@contextmanager
def open_database(project_dir: str | Path) -> Iterator[sqlite3.Connection]:
    conn = connect(project_dir)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def parse_date(value: str) -> str:
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid date {value!r}; expected YYYY-MM-DD") from exc
    return parsed.isoformat()


def parse_positive_float(value: str, field: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field}: {value!r}") from exc
    if parsed <= 0:
        raise ValueError(f"{field} must be positive: {value!r}")
    return parsed


def parse_non_negative_float(value: str, field: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field}: {value!r}") from exc
    if parsed < 0:
        raise ValueError(f"{field} must be non-negative: {value!r}")
    return parsed


def iter_business_days(start: dt.date, count: int) -> list[dt.date]:
    days: list[dt.date] = []
    current = start
    while len(days) < count:
        if current.weekday() < 5:
            days.append(current)
        current += dt.timedelta(days=1)
    return days


def generate_sample_csv(project_dir: str | Path, rows_per_asset: int = 560) -> Path:
    root = ensure_project(project_dir)
    config = load_config(root)
    path = root / "data" / "sample_prices.csv"
    days = iter_business_days(dt.date(2022, 1, 3), rows_per_asset)
    parameters = {
        "sp500": (100.0, 0.00055, 0.018),
        "nasdaq100": (90.0, 0.00070, 0.026),
        "hs300": (80.0, 0.00036, 0.032),
        "csi500": (70.0, 0.00045, 0.038),
    }
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "asset_id", "close", "volume"])
        writer.writeheader()
        for asset_id in asset_ids(config):
            start, drift, amplitude = parameters.get(asset_id, (100.0, 0.00035, 0.02))
            for index, day in enumerate(days):
                cycle = math.sin(index / 33.0) * amplitude
                slow_cycle = math.sin(index / 111.0) * amplitude * 1.7
                price = start * ((1 + drift) ** index) * (1 + cycle + slow_cycle)
                volume = 1_000_000 + (index % 37) * 10_000
                writer.writerow(
                    {
                        "date": day.isoformat(),
                        "asset_id": asset_id,
                        "close": f"{price:.4f}",
                        "volume": f"{volume:.0f}",
                    }
                )
    return path


def import_price_csv(project_dir: str | Path, csv_path: str | Path) -> int:
    root = ensure_project(project_dir)
    config = load_config(root)
    allowed = set(asset_ids(config))
    path = Path(csv_path).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"CSV file does not exist: {path}")

    rows: list[tuple[str, str, float, float | None]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"date", "asset_id", "close"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV must contain columns: {', '.join(sorted(required))}")
        for raw in reader:
            asset_id = (raw.get("asset_id") or "").strip()
            if asset_id not in allowed:
                raise ValueError(f"Unknown asset_id {asset_id!r}; update config.json first")
            date = parse_date((raw.get("date") or "").strip())
            close = parse_positive_float((raw.get("close") or "").strip(), "close")
            volume_raw = (raw.get("volume") or "").strip()
            volume = parse_non_negative_float(volume_raw, "volume") if volume_raw else None
            rows.append((asset_id, date, close, volume))

    if not rows:
        raise ValueError(f"No price rows found in {path}")

    with open_database(root) as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO price_daily (asset_id, date, close, volume)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
    return len(rows)


def initialize_database(project_dir: str | Path, sample: bool = False, csv_file: str | Path | None = None) -> dict[str, Any]:
    root = ensure_project(project_dir)
    with open_database(root):
        pass
    imported = 0
    sample_path: str | None = None
    if sample:
        generated = generate_sample_csv(root)
        sample_path = str(generated)
        imported += import_price_csv(root, generated)
    if csv_file is not None:
        imported += import_price_csv(root, csv_file)
    return {"database": str(db_path(root)), "imported_rows": imported, "sample_csv": sample_path}


def validate_data(project_dir: str | Path) -> dict[str, Any]:
    root = project_root(project_dir)
    config = load_config(root)
    min_history = int(config["strategy"].get("min_history_days", 320))
    with open_database(root) as conn:
        rows = conn.execute(
            """
            SELECT asset_id, COUNT(*) AS row_count, MIN(date) AS first_date, MAX(date) AS last_date
            FROM price_daily
            GROUP BY asset_id
            ORDER BY asset_id
            """
        ).fetchall()

    by_asset = {
        row["asset_id"]: {
            "row_count": int(row["row_count"]),
            "first_date": row["first_date"],
            "last_date": row["last_date"],
            "meets_min_history": int(row["row_count"]) >= min_history,
        }
        for row in rows
    }
    for asset_id in asset_ids(config):
        by_asset.setdefault(
            asset_id,
            {
                "row_count": 0,
                "first_date": None,
                "last_date": None,
                "meets_min_history": False,
            },
        )

    ok = all(item["meets_min_history"] for item in by_asset.values())
    result = {"ok": ok, "min_history_days": min_history, "assets": by_asset}
    write_json(root / "reports" / "data-health.json", result)
    return result


def load_series(conn: sqlite3.Connection, ids: list[str]) -> dict[str, list[PricePoint]]:
    result: dict[str, list[PricePoint]] = {}
    for asset_id in ids:
        rows = conn.execute(
            "SELECT date, close, volume FROM price_daily WHERE asset_id = ? ORDER BY date",
            (asset_id,),
        ).fetchall()
        result[asset_id] = [
            PricePoint(row["date"], float(row["close"]), None if row["volume"] is None else float(row["volume"]))
            for row in rows
        ]
    return result


def point_index_on_or_before(points: list[PricePoint], date: str) -> int | None:
    dates = [point.date for point in points]
    index = bisect.bisect_right(dates, date) - 1
    return index if index >= 0 else None


def close_on_or_before(points: list[PricePoint], date: str) -> float | None:
    index = point_index_on_or_before(points, date)
    if index is None:
        return None
    return points[index].close


def monthly_signal_dates(series: dict[str, list[PricePoint]]) -> list[str]:
    all_dates = sorted({point.date for points in series.values() for point in points})
    result: list[str] = []
    for index, date in enumerate(all_dates):
        next_date = all_dates[index + 1] if index + 1 < len(all_dates) else None
        if next_date is None or next_date[:7] != date[:7]:
            result.append(date)
    return result


def select_signal(series: dict[str, list[PricePoint]], config: dict[str, Any], as_of: str) -> dict[str, Any]:
    strategy = config["strategy"]
    lookback = int(strategy.get("lookback_days", 252))
    skip = int(strategy.get("skip_recent_days", 21))
    moving_average = int(strategy.get("moving_average_days", 160))
    breadth_min_ratio = float(strategy.get("breadth_min_ratio", 0.33))
    fallback_asset = str(strategy.get("fallback_asset", "cash"))

    candidates: list[dict[str, Any]] = []
    enough_assets = 0
    for asset_id in asset_ids(config):
        points = series.get(asset_id, [])
        index = point_index_on_or_before(points, as_of)
        if index is None:
            continue
        if index < max(lookback, moving_average - 1) or index - skip < 0:
            continue
        enough_assets += 1
        now = points[index].close
        recent = points[index - skip].close
        older = points[index - lookback].close
        ma_slice = points[index - moving_average + 1 : index + 1]
        moving_average_value = sum(point.close for point in ma_slice) / len(ma_slice)
        momentum = recent / older - 1
        trend_ok = now > moving_average_value
        if momentum > 0 and trend_ok:
            candidates.append(
                {
                    "asset_id": asset_id,
                    "momentum": momentum,
                    "close": now,
                    "moving_average": moving_average_value,
                }
            )

    breadth = (len(candidates) / enough_assets) if enough_assets else 0.0
    if not candidates or breadth < breadth_min_ratio:
        selected = fallback_asset if fallback_asset in series and close_on_or_before(series[fallback_asset], as_of) else "cash"
        reason = "fallback"
    else:
        selected = max(candidates, key=lambda item: item["momentum"])["asset_id"]
        reason = "momentum_winner"

    return {
        "as_of": as_of,
        "selected_asset": selected,
        "reason": reason,
        "breadth": breadth,
        "eligible_assets": len(candidates),
        "assets_with_enough_history": enough_assets,
        "candidates": sorted(candidates, key=lambda item: item["momentum"], reverse=True),
        "target_weights": {selected: 1.0} if selected != "cash" else {"cash": 1.0},
    }


def max_drawdown(equity: list[float]) -> float:
    peak = equity[0]
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1)
    return worst


def run_backtest(project_dir: str | Path) -> dict[str, Any]:
    root = project_root(project_dir)
    config = load_config(root)
    with open_database(root) as conn:
        series = load_series(conn, asset_ids(config))

    dates = monthly_signal_dates(series)
    if len(dates) < 2:
        raise ValueError("Not enough price history to run a backtest")

    equity = 1.0
    equity_curve = [equity]
    period_returns: list[float] = []
    signals: list[dict[str, Any]] = []
    previous_asset: str | None = None
    turnover_events = 0

    for start_date, end_date in zip(dates[:-1], dates[1:]):
        signal = select_signal(series, config, start_date)
        asset_id = signal["selected_asset"]
        if asset_id == "cash":
            period_return = 0.0
        else:
            start_close = close_on_or_before(series[asset_id], start_date)
            end_close = close_on_or_before(series[asset_id], end_date)
            if start_close is None or end_close is None or start_close <= 0:
                period_return = 0.0
            else:
                period_return = end_close / start_close - 1
        equity *= 1 + period_return
        equity_curve.append(equity)
        period_returns.append(period_return)
        if previous_asset is not None and previous_asset != asset_id:
            turnover_events += 1
        previous_asset = asset_id
        signals.append(
            {
                "signal_date": start_date,
                "next_date": end_date,
                "selected_asset": asset_id,
                "reason": signal["reason"],
                "breadth": signal["breadth"],
                "period_return": period_return,
                "equity": equity,
            }
        )

    start = dt.date.fromisoformat(signals[0]["signal_date"])
    end = dt.date.fromisoformat(signals[-1]["next_date"])
    years = max((end - start).days / 365.25, 1 / 365.25)
    cagr = equity ** (1 / years) - 1
    mean_return = sum(period_returns) / len(period_returns)
    if len(period_returns) > 1:
        variance = sum((item - mean_return) ** 2 for item in period_returns) / (len(period_returns) - 1)
        stdev = math.sqrt(variance)
    else:
        stdev = 0.0
    sharpe = (mean_return * 12) / (stdev * math.sqrt(12)) if stdev > 0 else 0.0
    summary = {
        "status": "research_only",
        "disclaimer": DISCLAIMER,
        "start_date": signals[0]["signal_date"],
        "end_date": signals[-1]["next_date"],
        "periods": len(signals),
        "final_equity": equity,
        "cagr": cagr,
        "max_drawdown": max_drawdown(equity_curve),
        "sharpe_like": sharpe,
        "turnover_events": turnover_events,
    }
    reports = root / "reports"
    write_json(reports / "backtest-summary.json", summary)
    with (reports / "signals.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(signals[0].keys()))
        writer.writeheader()
        writer.writerows(signals)
    return summary


def initialize_wallet(project_dir: str | Path, capital: float) -> dict[str, Any]:
    if capital <= 0:
        raise ValueError("capital must be positive")
    root = ensure_project(project_dir)
    with open_database(root) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO wallet_settings (key, value) VALUES (?, ?)",
            ("starting_cash", f"{capital:.2f}"),
        )
    template = root / "wallet" / "transactions.example.csv"
    with template.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "asset_id", "side", "quantity", "price", "fee", "note"])
        writer.writeheader()
        writer.writerow(
            {
                "date": dt.date.today().isoformat(),
                "asset_id": "sp500",
                "side": "buy",
                "quantity": "100",
                "price": "1.23",
                "fee": "1.00",
                "note": "initial paper trade record",
            }
        )
    return {"wallet": str(db_path(root)), "starting_cash": capital, "template": str(template)}


def wallet_state(conn: sqlite3.Connection, series: dict[str, list[PricePoint]], as_of: str) -> dict[str, Any]:
    setting = conn.execute("SELECT value FROM wallet_settings WHERE key = ?", ("starting_cash",)).fetchone()
    if setting is None:
        return {"initialized": False, "cash": 0.0, "positions": {}, "market_value": 0.0, "total_value": 0.0}
    cash = float(setting["value"])
    positions: dict[str, float] = {}
    transactions = conn.execute(
        "SELECT asset_id, side, quantity, price, fee FROM wallet_transactions ORDER BY date, id"
    ).fetchall()
    for tx in transactions:
        asset_id = tx["asset_id"]
        quantity = float(tx["quantity"])
        price = float(tx["price"])
        fee = float(tx["fee"])
        if tx["side"] == "buy":
            cash -= quantity * price + fee
            positions[asset_id] = positions.get(asset_id, 0.0) + quantity
        else:
            cash += quantity * price - fee
            positions[asset_id] = positions.get(asset_id, 0.0) - quantity

    values: dict[str, dict[str, float]] = {}
    market_value = 0.0
    for asset_id, quantity in positions.items():
        if abs(quantity) < 1e-9:
            continue
        price = close_on_or_before(series.get(asset_id, []), as_of)
        value = quantity * price if price is not None else 0.0
        market_value += value
        values[asset_id] = {"quantity": quantity, "price": price or 0.0, "value": value}
    return {
        "initialized": True,
        "cash": cash,
        "positions": values,
        "market_value": market_value,
        "total_value": cash + market_value,
    }


def latest_common_signal_date(series: dict[str, list[PricePoint]], config: dict[str, Any]) -> str:
    latest = [points[-1].date for asset_id, points in series.items() if asset_id in asset_ids(config) and points]
    if not latest:
        raise ValueError("No price data found")
    return min(latest)


def build_action_packet(project_dir: str | Path) -> dict[str, Any]:
    root = project_root(project_dir)
    config = load_config(root)
    data_health = validate_data(root)
    with open_database(root) as conn:
        series = load_series(conn, asset_ids(config))
        signal_date = latest_common_signal_date(series, config)
        signal = select_signal(series, config, signal_date)
        wallet = wallet_state(conn, series, signal_date)

    trades: list[dict[str, Any]] = []
    min_trade_value = float(config["strategy"].get("min_trade_value", 100.0))
    if wallet["initialized"] and wallet["total_value"] > 0:
        total_value = float(wallet["total_value"])
        current_values = {asset_id: data["value"] for asset_id, data in wallet["positions"].items()}
        target_weights = signal["target_weights"]
        target_assets = set(target_weights)
        all_trade_assets = set(current_values) | {asset for asset in target_assets if asset != "cash"}
        for asset_id in sorted(all_trade_assets):
            price = close_on_or_before(series.get(asset_id, []), signal_date)
            if price is None or price <= 0:
                continue
            current_value = current_values.get(asset_id, 0.0)
            target_value = total_value * float(target_weights.get(asset_id, 0.0))
            delta = target_value - current_value
            if abs(delta) < min_trade_value:
                continue
            trades.append(
                {
                    "asset_id": asset_id,
                    "side": "buy" if delta > 0 else "sell",
                    "estimated_value": abs(delta),
                    "estimated_quantity": abs(delta) / price,
                    "reference_price": price,
                }
            )

    packet = {
        "status": "research_only",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "disclaimer": DISCLAIMER,
        "signal_date": signal_date,
        "signal": signal,
        "target_weights": signal["target_weights"],
        "data_health": data_health,
        "portfolio": wallet,
        "recommended_trades": trades,
    }
    write_json(root / "reports" / "latest-action.json", packet)
    return packet


def read_csv_tail(path: Path, limit: int = 6) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return rows[-limit:]


def collect_ai_research_context(project_dir: str | Path) -> dict[str, Any]:
    root = project_root(project_dir)
    reports = root / "reports"
    packet_path = reports / "latest-action.json"
    summary_path = reports / "backtest-summary.json"
    health_path = reports / "data-health.json"
    signals_path = reports / "signals.csv"

    if not packet_path.exists():
        build_action_packet(root)
    if not summary_path.exists():
        run_backtest(root)
    if not health_path.exists():
        validate_data(root)

    packet = read_json(packet_path)
    summary = read_json(summary_path)
    health = read_json(health_path)
    signals_tail = read_csv_tail(signals_path)
    return {
        "disclaimer": DISCLAIMER,
        "source_files": [
            str(packet_path),
            str(summary_path),
            str(health_path),
            str(signals_path),
        ],
        "action_packet": packet,
        "backtest_summary": summary,
        "data_health": health,
        "recent_signals": signals_tail,
    }


def build_ai_research_prompt(context: dict[str, Any]) -> list[dict[str, str]]:
    compact_context = {
        "disclaimer": context["disclaimer"],
        "action_packet": context["action_packet"],
        "backtest_summary": context["backtest_summary"],
        "data_health": context["data_health"],
        "recent_signals": context["recent_signals"],
    }
    return [
        {"role": "system", "content": AI_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Write a concise Chinese research brief from this local Apex workspace context. "
                "Cover current signal, data quality, backtest caveats, paper-wallet drift, and next checks. "
                "Keep it research-only and avoid trade instructions.\n\n"
                + json.dumps(compact_context, ensure_ascii=False, indent=2)
            ),
        },
    ]


def call_openai_compatible_chat(
    messages: list[dict[str, str]],
    api_key: str,
    base_url: str,
    model: str,
    timeout: float = 30.0,
) -> str:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 900,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"AI request failed with HTTP {exc.code}: {body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"AI request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise ValueError("AI request timed out") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("AI response was not valid JSON") from exc
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("AI response did not contain message content") from exc
    if not isinstance(content, str) or not content.strip():
        raise ValueError("AI response content was empty")
    return content.strip()


def generate_ai_research_brief(
    project_dir: str | Path,
    base_url: str | None = None,
    model: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    root = project_root(project_dir)
    context = collect_ai_research_context(root)
    resolved_base_url = base_url or os.environ.get("APEX_AI_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or DEFAULT_AI_BASE_URL
    resolved_model = model or os.environ.get("APEX_AI_MODEL") or os.environ.get("OPENAI_MODEL") or DEFAULT_AI_MODEL

    api_key = os.environ.get("APEX_AI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("缺少 AI 接口密钥。请设置 APEX_AI_API_KEY 或 OPENAI_API_KEY。")
    messages = build_ai_research_prompt(context)
    brief = call_openai_compatible_chat(messages, api_key, resolved_base_url, resolved_model, timeout=timeout)
    status = "ai_generated"

    packet = context["action_packet"]
    summary = context["backtest_summary"]
    health = context["data_health"]
    record = {
        "status": status,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": "openai_compatible_chat_completions",
        "base_url": resolved_base_url,
        "model": resolved_model,
        "disclaimer": DISCLAIMER,
        "source_files": context["source_files"],
        "input_summary": {
            "signal_date": packet.get("signal_date"),
            "selected_asset": packet.get("signal", {}).get("selected_asset"),
            "signal_reason": packet.get("signal", {}).get("reason"),
            "data_ok": health.get("ok"),
            "backtest_periods": summary.get("periods"),
            "recommended_trade_count": len(packet.get("recommended_trades", [])),
        },
        "brief_markdown": brief,
    }
    reports = root / "reports"
    json_path = reports / "ai-brief.json"
    md_path = reports / "ai-brief.md"
    write_json(json_path, record)
    md_path.write_text(
        "# AI 研究解读\n\n"
        f"{DISCLAIMER}\n\n"
        f"- 生成时间：{record['generated_at']}\n"
        f"- 模型：{resolved_model}\n"
        "- 状态：已生成\n\n"
        "## 解读正文\n\n"
        f"{brief}\n",
        encoding="utf-8",
    )
    return {"ai_brief_json": str(json_path), "ai_brief_md": str(md_path), "status": status}


def scaffold_web(project_dir: str | Path) -> dict[str, Any]:
    root = project_root(project_dir)
    packet_path = root / "reports" / "latest-action.json"
    if not packet_path.exists():
        build_action_packet(root)
    summary_path = root / "reports" / "backtest-summary.json"
    if not summary_path.exists():
        run_backtest(root)

    packet = read_json(packet_path)
    summary = read_json(summary_path)
    ai_brief_path = root / "reports" / "ai-brief.json"
    ai_brief = read_json(ai_brief_path) if ai_brief_path.exists() else None
    skill_dir = Path(__file__).resolve().parents[1]
    template = (skill_dir / "assets" / "web-template" / "index.html").read_text(encoding="utf-8")
    rendered = (
        template.replace("__ACTION_JSON__", json.dumps(packet, ensure_ascii=False))
        .replace("__SUMMARY_JSON__", json.dumps(summary, ensure_ascii=False))
        .replace("__AI_BRIEF_JSON__", json.dumps(ai_brief, ensure_ascii=False))
    )
    output = root / "web" / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    return {"web_index": str(output)}


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def run_cli(fn: Any, args: argparse.Namespace) -> int:
    configure_stdio()
    try:
        print_json(fn(args))
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
