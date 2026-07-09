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


RESEARCH_USE_DISCLAIMER = (
    "本地研究输出，仅用于研究，不构成个性化投资建议、实盘表现或交易指令。"
)
DISCLAIMER = RESEARCH_USE_DISCLAIMER
DEFAULT_MIN_HISTORY_DAYS = 320
DEFAULT_MIN_PAPER_REBALANCE_AMOUNT = 100.0
DEFAULT_SAMPLE_ROWS_PER_ASSET = 560
WORKSPACE_DIRS = ("data", "reports", "wallet", "web", "logs")

CONFIG_FILENAME = "config.json"
DATABASE_FILENAME = "apex.sqlite"
SAMPLE_PRICES_FILENAME = "sample_prices.csv"
PAPER_TRANSACTION_TEMPLATE_FILENAME = "transactions.example.csv"
DATA_HEALTH_REPORT_FILENAME = "data-health.json"
MOMENTUM_SUMMARY_FILENAME = "backtest-summary.json"
MOMENTUM_SIGNALS_FILENAME = "signals.csv"
RESEARCH_PACKET_FILENAME = "latest-action.json"
AI_BRIEF_JSON_FILENAME = "ai-brief.json"
AI_BRIEF_MARKDOWN_FILENAME = "ai-brief.md"
SOFTWARE_NAME = "Apex资产动量研究与AI解读软件"
SOFTWARE_VERSION = "V1.2.0"

BRAND_ORANGE = "\033[38;5;208m"
BRAND_GOLD = "\033[38;5;220m"
BRAND_DIM = "\033[2m"
BRAND_BOLD = "\033[1m"
BRAND_RESET = "\033[0m"

BRAND_LOGO = (
    "    ___    ____  _______  __",
    "   /   |  / __ \\/ ____/ |/ /",
    "  / /| | / /_/ / __/  |   / ",
    " / ___ |/ ____/ /___ /   |  ",
    "/_/  |_/_/   /_____//_/|_|  ",
)

ASSET_DISPLAY_NAMES = {
    "bse50": "北证50",
    "cash": "现金",
    "chinext": "创业板",
    "consumer": "消费",
    "csi500": "中证500",
    "csi_div": "红利",
    "financials": "金融",
    "healthcare": "医药",
    "hs300": "沪深300",
    "infotech": "信息技术",
    "military": "军工",
    "nasdaq100": "纳斯达克100",
    "newenergy": "新能源",
    "nonferrous": "有色金属",
    "realestate": "房地产",
    "semiconductor": "半导体",
    "sp500": "标普500",
    "sse50": "上证50",
}
TERMINAL_VALUE_LABELS = {
    "initialized": "已初始化",
    "research_only": "研究模式",
    "apex17": "公开 17 标的",
    "minimal": "演示配置",
    "fallback": "保守回退",
}

CSV_REQUIRED_PRICE_COLUMNS = {"date", "asset_id", "close"}
FIELD_LABELS = {
    "date": "日期(date)",
    "asset_id": "标的代码(asset_id)",
    "close": "收盘价(close)",
    "volume": "成交量(volume)",
    "capital": "纸面钱包初始资金",
    "quantity": "交易数量(quantity)",
    "price": "成交价格(price)",
    "fee": "交易费用(fee)",
}

AI_SYSTEM_PROMPT = (
    "You are the AI research interpretation layer inside a local momentum research tool. "
    "Explain only the provided local research outputs. Do not provide personalized financial advice, "
    "do not tell the user to buy or sell, do not promise returns, do not invent missing data, "
    "and never override the original signal, data-health result, or paper rebalance table."
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
        "min_history_days": DEFAULT_MIN_HISTORY_DAYS,
        "min_trade_value": DEFAULT_MIN_PAPER_REBALANCE_AMOUNT,
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
        "min_history_days": DEFAULT_MIN_HISTORY_DAYS,
        "min_trade_value": DEFAULT_MIN_PAPER_REBALANCE_AMOUNT,
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


def terminal_color_enabled(stream: Any = sys.stderr) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("APEX_FORCE_COLOR") == "1":
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def use_terminal_report() -> bool:
    if os.environ.get("APEX_OUTPUT_JSON") == "1":
        return False
    if os.environ.get("APEX_FORCE_TERMINAL") == "1":
        return True
    return bool(sys.stdout.isatty() or sys.stderr.isatty())


def colorize(text: str, color_code: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{color_code}{text}{BRAND_RESET}"


def display_asset(asset_id: Any) -> str:
    if not isinstance(asset_id, str):
        return str(asset_id)
    return ASSET_DISPLAY_NAMES.get(asset_id, asset_id)


def format_terminal_value(value: Any) -> str:
    if isinstance(value, bool):
        return "通过" if value else "未通过"
    if isinstance(value, float):
        if -1 <= value <= 1:
            return f"{value:.2%}"
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, dict):
        if not value:
            return "无"
        parts = []
        for key, val in value.items():
            formatted = format_terminal_value(val)
            parts.append(f"{display_asset(key)} {formatted}")
        return " / ".join(parts[:4])
    if isinstance(value, list):
        return f"{len(value)} 项" if value else "无"
    if value is None:
        return "无"
    text = str(value)
    if text in TERMINAL_VALUE_LABELS:
        return TERMINAL_VALUE_LABELS[text]
    if len(text) > 76 and ("\\" in text or "/" in text):
        return "..." + text[-73:]
    if len(text) > 96:
        return text[:93] + "..."
    return text


def terminal_highlights(result: dict[str, Any]) -> list[tuple[str, Any]]:
    derived: list[tuple[str, Any]] = []
    assets = result.get("assets")
    if isinstance(assets, dict) and assets:
        enough = sum(1 for item in assets.values() if isinstance(item, dict) and item.get("meets_min_history"))
        derived.append(("检查资产", len(assets)))
        derived.append(("达标资产", enough))
        sample_asset_id, sample = next(iter(assets.items()))
        if isinstance(sample, dict):
            derived.append(
                (
                    "样例区间",
                    (
                        f"{display_asset(sample_asset_id)} "
                        f"{sample.get('row_count', 0)} 行 | "
                        f"{sample.get('first_date', '未知')} 至 {sample.get('last_date', '未知')}"
                    ),
                )
            )
    candidates = [
        ("status", "状态"),
        ("ok", "数据校验"),
        ("message", "提示"),
        ("project_dir", "研究工作区"),
        ("profile", "配置轮廓"),
        ("database", "数据库"),
        ("imported_rows", "导入记录"),
        ("min_history_days", "最低历史"),
        ("assets_checked", "检查资产"),
        ("assets_with_enough_history", "达标资产"),
        ("start_date", "开始日期"),
        ("end_date", "结束日期"),
        ("periods", "调仓期数"),
        ("final_equity", "最终权益"),
        ("cagr", "年化收益"),
        ("max_drawdown", "最大回撤"),
        ("wallet", "纸面钱包"),
        ("starting_cash", "起始资金"),
        ("template", "交易模板"),
        ("signal_date", "信号日期"),
        ("selected_asset", "当前标的"),
        ("signal_reason", "触发原因"),
        ("target_weights", "目标权重"),
        ("paper_rebalance_rows", "纸面调仓"),
        ("ai_brief_md", "研究简报"),
        ("model", "模型"),
        ("web_index", "网页报告"),
    ]
    highlights: list[tuple[str, Any]] = []
    for key, label in candidates:
        if key in result:
            value = result[key]
            if key == "selected_asset":
                value = display_asset(value)
            highlights.append((label, value))
            if key == "min_history_days":
                highlights.extend(derived)
                derived = []
    highlights.extend(derived)
    return highlights[:9]


def print_terminal_report(title: str, result: dict[str, Any], stream: Any = sys.stderr) -> None:
    colors = terminal_color_enabled(stream)
    print(colorize(BRAND_LOGO[0], BRAND_ORANGE, colors), file=stream)
    for line in BRAND_LOGO[1:]:
        print(colorize(line, BRAND_ORANGE, colors), file=stream)
    print(colorize(f"{SOFTWARE_NAME}  {SOFTWARE_VERSION}", BRAND_BOLD, colors), file=stream)
    print(colorize("APEX 研究控制台 | 本地资产动量研究台 | 仅研究用途 | 不连接券商", BRAND_DIM, colors), file=stream)
    print(colorize(f"> {title}", BRAND_GOLD, colors), file=stream)
    print("", file=stream)
    print(colorize("运行结果", BRAND_BOLD, colors), file=stream)
    for label, value in terminal_highlights(result):
        print(f"  {label:<10} {format_terminal_value(value)}", file=stream)
    print("", file=stream)


def project_root(project_dir: str | Path) -> Path:
    return Path(project_dir).expanduser().resolve()


def config_path(project_dir: str | Path) -> Path:
    return project_root(project_dir) / CONFIG_FILENAME


def db_path(project_dir: str | Path) -> Path:
    return project_root(project_dir) / "data" / DATABASE_FILENAME


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config(project_dir: str | Path) -> dict[str, Any]:
    path = config_path(project_dir)
    if not path.exists():
        raise ValueError(f"缺少 {CONFIG_FILENAME}。请先运行 apex init 初始化本地研究工作区：{path}")
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
    raise ValueError("未知工作区画像。请使用 'minimal' 或 'apex17'。")


def ensure_project(project_dir: str | Path, overwrite: bool = False, profile: str = "minimal") -> Path:
    root = project_root(project_dir)
    root.mkdir(parents=True, exist_ok=True)
    for dirname in WORKSPACE_DIRS:
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
        raise ValueError(f"日期格式无效：{value!r}；请使用 YYYY-MM-DD。") from exc
    return parsed.isoformat()


def field_label(field: str) -> str:
    return FIELD_LABELS.get(field, field)


def coerce_finite_number(value: Any, field: str) -> float:
    label = field_label(field)
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}必须是数字：{value!r}") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{label}必须是有限数字：{value!r}")
    return parsed


def parse_positive_float(value: str, field: str) -> float:
    parsed = coerce_finite_number(value, field)
    if parsed <= 0:
        raise ValueError(f"{field_label(field)}必须大于 0：{value!r}")
    return parsed


def parse_non_negative_float(value: str, field: str) -> float:
    parsed = coerce_finite_number(value, field)
    if parsed < 0:
        raise ValueError(f"{field_label(field)}不能为负数：{value!r}")
    return parsed


def ensure_positive_number(value: Any, field: str) -> float:
    parsed = coerce_finite_number(value, field)
    if parsed <= 0:
        raise ValueError(f"{field_label(field)}必须大于 0：{value!r}")
    return parsed


def ensure_non_negative_number(value: Any, field: str) -> float:
    parsed = coerce_finite_number(value, field)
    if parsed < 0:
        raise ValueError(f"{field_label(field)}不能为负数：{value!r}")
    return parsed


def iter_business_days(start: dt.date, count: int) -> list[dt.date]:
    days: list[dt.date] = []
    current = start
    while len(days) < count:
        if current.weekday() < 5:
            days.append(current)
        current += dt.timedelta(days=1)
    return days


def generate_sample_csv(project_dir: str | Path, rows_per_asset: int = DEFAULT_SAMPLE_ROWS_PER_ASSET) -> Path:
    root = ensure_project(project_dir)
    config = load_config(root)
    path = root / "data" / SAMPLE_PRICES_FILENAME
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
                # 示例数据只保证流程可演示，真实研究必须替换为用户审阅过的价格 CSV。
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
        raise ValueError(f"CSV 文件不存在：{path}")

    rows: list[tuple[str, str, float, float | None]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(CSV_REQUIRED_PRICE_COLUMNS - fieldnames)
        if missing:
            raise ValueError(
                "CSV 字段缺失：缺少 "
                f"{', '.join(missing)}；请提供 date、asset_id、close 三列，volume 可选。文件：{path}"
            )
        for row_number, raw in enumerate(reader, start=2):
            try:
                asset_id = (raw.get("asset_id") or "").strip()
                if asset_id not in allowed:
                    raise ValueError(f"未配置的标的代码 {asset_id!r}；请先在 {CONFIG_FILENAME} 的 assets 中登记。")
                date = parse_date((raw.get("date") or "").strip())
                close = parse_positive_float((raw.get("close") or "").strip(), "close")
                volume_raw = (raw.get("volume") or "").strip()
                volume = parse_non_negative_float(volume_raw, "volume") if volume_raw else None
            except ValueError as exc:
                raise ValueError(f"CSV 第 {row_number} 行错误：{exc}") from exc
            rows.append((asset_id, date, close, volume))

    if not rows:
        raise ValueError(f"CSV 没有可导入的价格记录：{path}")

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

    short_assets = [
        asset_id
        for asset_id, item in by_asset.items()
        if not item["meets_min_history"]
    ]
    ok = not short_assets
    message = (
        f"数据覆盖满足最低历史要求：每个标的至少 {min_history} 个交易日。"
        if ok
        else (
            f"历史数据不足：{len(short_assets)} 个标的未达到 {min_history} 个交易日；"
            "请补充价格 CSV 后再运行回测、行动建议包或 AI 解读。"
        )
    )
    result = {"ok": ok, "message": message, "min_history_days": min_history, "assets": by_asset}
    write_json(root / "reports" / DATA_HEALTH_REPORT_FILENAME, result)
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
        data_health = validate_data(root)
        raise ValueError(f"价格历史不足，无法运行研究回测：{data_health['message']}")

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
    momentum_summary = {
        "status": "research_only",
        "status_label": "仅研究用途",
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
    write_json(reports / MOMENTUM_SUMMARY_FILENAME, momentum_summary)
    with (reports / MOMENTUM_SIGNALS_FILENAME).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(signals[0].keys()))
        writer.writeheader()
        writer.writerows(signals)
    return momentum_summary


def initialize_wallet(project_dir: str | Path, capital: float) -> dict[str, Any]:
    capital_value = ensure_positive_number(capital, "capital")
    root = ensure_project(project_dir)
    with open_database(root) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO wallet_settings (key, value) VALUES (?, ?)",
            ("starting_cash", f"{capital_value:.2f}"),
        )
    # 公开包只维护纸面钱包；券商连接会把真实账户状态和凭证混入研究流程。
    template = root / "wallet" / PAPER_TRANSACTION_TEMPLATE_FILENAME
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
    return {"wallet": str(db_path(root)), "starting_cash": capital_value, "template": str(template)}


def wallet_state(conn: sqlite3.Connection, series: dict[str, list[PricePoint]], as_of: str) -> dict[str, Any]:
    setting = conn.execute("SELECT value FROM wallet_settings WHERE key = ?", ("starting_cash",)).fetchone()
    if setting is None:
        return {"initialized": False, "cash": 0.0, "positions": {}, "market_value": 0.0, "total_value": 0.0}
    cash = ensure_non_negative_number(setting["value"], "capital")
    positions: dict[str, float] = {}
    transactions = conn.execute(
        "SELECT asset_id, side, quantity, price, fee FROM wallet_transactions ORDER BY date, id"
    ).fetchall()
    for tx in transactions:
        asset_id = tx["asset_id"]
        quantity = ensure_non_negative_number(tx["quantity"], "quantity")
        price = ensure_non_negative_number(tx["price"], "price")
        fee = ensure_non_negative_number(tx["fee"], "fee")
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
        raise ValueError("未找到价格数据。请先导入价格 CSV，或用 --sample 生成流程演示数据。")
    return min(latest)


def build_action_packet(project_dir: str | Path) -> dict[str, Any]:
    root = project_root(project_dir)
    config = load_config(root)
    data_health = validate_data(root)
    with open_database(root) as conn:
        series = load_series(conn, asset_ids(config))
        signal_date = latest_common_signal_date(series, config)
        signal = select_signal(series, config, signal_date)
        paper_wallet = wallet_state(conn, series, signal_date)

    paper_rebalance_rows: list[dict[str, Any]] = []
    min_trade_value = ensure_positive_number(
        config["strategy"].get("min_trade_value", DEFAULT_MIN_PAPER_REBALANCE_AMOUNT),
        "min_trade_value",
    )
    if paper_wallet["initialized"] and paper_wallet["total_value"] > 0:
        total_value = ensure_positive_number(paper_wallet["total_value"], "capital")
        current_values = {asset_id: data["value"] for asset_id, data in paper_wallet["positions"].items()}
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
            # 低于阈值的差额不生成纸面调仓行，避免把零碎偏离伪装成可执行动作。
            if abs(delta) < min_trade_value:
                continue
            paper_rebalance_rows.append(
                {
                    "asset_id": asset_id,
                    "side": "buy" if delta > 0 else "sell",
                    "estimated_value": abs(delta),
                    "estimated_quantity": abs(delta) / price,
                    "reference_price": price,
                }
            )

    research_packet = {
        "status": "research_only",
        "status_label": "仅研究用途",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "disclaimer": DISCLAIMER,
        "signal_date": signal_date,
        "signal": signal,
        "target_weights": signal["target_weights"],
        "data_health": data_health,
        "portfolio": paper_wallet,
        "paper_wallet": paper_wallet,
        "paper_rebalance_rows": paper_rebalance_rows,
        "recommended_trades": paper_rebalance_rows,
    }
    write_json(root / "reports" / RESEARCH_PACKET_FILENAME, research_packet)
    return research_packet


def read_csv_tail(path: Path, limit: int = 6) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return rows[-limit:]


def collect_ai_research_context(project_dir: str | Path) -> dict[str, Any]:
    root = project_root(project_dir)
    reports = root / "reports"
    research_packet_path = reports / RESEARCH_PACKET_FILENAME
    momentum_summary_path = reports / MOMENTUM_SUMMARY_FILENAME
    health_path = reports / DATA_HEALTH_REPORT_FILENAME
    signals_path = reports / MOMENTUM_SIGNALS_FILENAME

    if not research_packet_path.exists():
        build_action_packet(root)
    if not momentum_summary_path.exists():
        run_backtest(root)
    if not health_path.exists():
        validate_data(root)

    research_packet = read_json(research_packet_path)
    momentum_summary = read_json(momentum_summary_path)
    health = read_json(health_path)
    signals_tail = read_csv_tail(signals_path)
    return {
        "disclaimer": DISCLAIMER,
        "source_files": [
            str(research_packet_path),
            str(momentum_summary_path),
            str(health_path),
            str(signals_path),
        ],
        "research_packet": research_packet,
        "action_packet": research_packet,
        "momentum_summary": momentum_summary,
        "backtest_summary": momentum_summary,
        "data_health": health,
        "recent_signals": signals_tail,
    }


def build_ai_research_prompt(context: dict[str, Any]) -> list[dict[str, str]]:
    research_packet = context.get("research_packet", context.get("action_packet"))
    momentum_summary = context.get("momentum_summary", context.get("backtest_summary"))
    compact_context = {
        "disclaimer": context["disclaimer"],
        "research_packet": research_packet,
        "momentum_summary": momentum_summary,
        "data_health": context["data_health"],
        "recent_signals": context["recent_signals"],
    }
    return [
        {"role": "system", "content": AI_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "请基于以下本地 Apex 研究工作区上下文，写一段简洁中文研究简报。"
                "覆盖当前信号、数据质量、回测限制、纸面钱包偏离和下一步核查。"
                "AI 解读只能解释原始研究文件，不能替代 research_packet、momentum_summary、"
                "data_health 或 paper_rebalance_rows，也不能写成交易指令。\n\n"
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
        raise ValueError(f"AI 解读请求失败（HTTP {exc.code}）：{body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"AI 解读请求失败：{exc.reason}") from exc
    except TimeoutError as exc:
        raise ValueError("AI 解读请求超时。请稍后重试，或调大 --timeout。") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("AI 接口返回内容不是有效 JSON。") from exc
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("AI 接口返回内容缺少 message.content。") from exc
    if not isinstance(content, str) or not content.strip():
        raise ValueError("AI 解读正文为空。")
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
        raise ValueError(
            "未检测到 AI 接口密钥。只使用本地信号、回测和网页报告可以跳过 AI 解读；"
            "如需生成解读，请设置 APEX_AI_API_KEY 或 OPENAI_API_KEY。"
        )
    messages = build_ai_research_prompt(context)
    brief = call_openai_compatible_chat(messages, api_key, resolved_base_url, resolved_model, timeout=timeout)
    status = "ai_generated"

    research_packet = context["research_packet"]
    momentum_summary = context["momentum_summary"]
    health = context["data_health"]
    paper_rebalance_rows = research_packet.get(
        "paper_rebalance_rows",
        research_packet.get("recommended_trades", []),
    )
    record = {
        "status": status,
        "status_label": "已生成",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": "openai_compatible_chat_completions",
        "base_url": resolved_base_url,
        "model": resolved_model,
        "disclaimer": DISCLAIMER,
        "source_files": context["source_files"],
        "input_summary": {
            "signal_date": research_packet.get("signal_date"),
            "selected_asset": research_packet.get("signal", {}).get("selected_asset"),
            "signal_reason": research_packet.get("signal", {}).get("reason"),
            "data_ok": health.get("ok"),
            "backtest_periods": momentum_summary.get("periods"),
            "paper_rebalance_count": len(paper_rebalance_rows),
        },
        "brief_markdown": brief,
    }
    reports = root / "reports"
    json_path = reports / AI_BRIEF_JSON_FILENAME
    md_path = reports / AI_BRIEF_MARKDOWN_FILENAME
    write_json(json_path, record)
    md_path.write_text(
        "# AI 研究解读\n\n"
        f"{DISCLAIMER}\n\n"
        "AI 解读只能解释本地研究输出，不能覆盖原始信号、数据健康结果或纸面调仓表。\n\n"
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
    research_packet_path = root / "reports" / RESEARCH_PACKET_FILENAME
    if not research_packet_path.exists():
        build_action_packet(root)
    momentum_summary_path = root / "reports" / MOMENTUM_SUMMARY_FILENAME
    if not momentum_summary_path.exists():
        run_backtest(root)

    research_packet = read_json(research_packet_path)
    momentum_summary = read_json(momentum_summary_path)
    ai_brief_path = root / "reports" / AI_BRIEF_JSON_FILENAME
    ai_brief = read_json(ai_brief_path) if ai_brief_path.exists() else None
    package_dir = Path(__file__).resolve().parents[1]
    template = (package_dir / "assets" / "web-template" / "index.html").read_text(encoding="utf-8")
    rendered = (
        template.replace("__ACTION_JSON__", json.dumps(research_packet, ensure_ascii=False))
        .replace("__SUMMARY_JSON__", json.dumps(momentum_summary, ensure_ascii=False))
        .replace("__AI_BRIEF_JSON__", json.dumps(ai_brief, ensure_ascii=False))
    )
    output = root / "web" / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    return {"web_index": str(output)}


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def run_cli(fn: Any, args: argparse.Namespace, title: str = "Apex 本地研究流程") -> int:
    configure_stdio()
    try:
        result = fn(args)
    except (ValueError, OSError, sqlite3.Error) as exc:
        if use_terminal_report():
            print_terminal_report(title, {"status": "运行失败", "message": str(exc)})
        else:
            print(f"错误：{exc}", file=sys.stderr)
        return 1
    if use_terminal_report():
        print_terminal_report(title, result)
    else:
        print_json(result)
    return 0
