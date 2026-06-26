from __future__ import annotations

import csv
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "apex-investment-strategy" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from apexlib import (  # noqa: E402
    build_action_packet,
    ensure_project,
    import_price_csv,
    initialize_database,
    initialize_wallet,
    run_backtest,
    scaffold_web,
    validate_data,
)


class ApexWorkflowTests(unittest.TestCase):
    def test_full_public_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "workspace"

            root = ensure_project(project)
            self.assertTrue((root / "config.json").exists())

            init_result = initialize_database(root, sample=True)
            self.assertGreater(init_result["imported_rows"], 1000)

            health = validate_data(root)
            self.assertTrue(health["ok"])
            self.assertIn("sp500", health["assets"])

            summary = run_backtest(root)
            self.assertEqual(summary["status"], "research_only")
            self.assertGreater(summary["periods"], 1)
            self.assertGreater(summary["final_equity"], 0)

            wallet = initialize_wallet(root, 100000)
            self.assertEqual(wallet["starting_cash"], 100000)

            packet = build_action_packet(root)
            self.assertEqual(packet["status"], "research_only")
            self.assertIn("target_weights", packet)
            self.assertTrue((root / "reports" / "latest-action.json").exists())

            web = scaffold_web(root)
            html = Path(web["web_index"]).read_text(encoding="utf-8")
            self.assertIn("Apex Investment Strategy", html)
            self.assertNotIn("__ACTION_JSON__", html)

    def test_validator_flags_missing_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "workspace"
            ensure_project(project)
            initialize_database(project)

            health = validate_data(project)
            self.assertFalse(health["ok"])
            self.assertEqual(health["assets"]["sp500"]["row_count"], 0)

    def test_import_rejects_unknown_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "workspace"
            ensure_project(project)
            initialize_database(project)
            bad_csv = project / "bad.csv"
            with bad_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["date", "asset_id", "close"])
                writer.writeheader()
                writer.writerow({"date": "2024-01-02", "asset_id": "unknown_asset", "close": "1.0"})

            with self.assertRaises(ValueError):
                import_price_csv(project, bad_csv)

    def test_database_schema_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "workspace"
            ensure_project(project)
            initialize_database(project)
            db = project / "data" / "apex.sqlite"

            conn = sqlite3.connect(db)
            try:
                tables = {
                    row[0]
                    for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
                }
            finally:
                conn.close()
            self.assertIn("price_daily", tables)
            self.assertIn("wallet_transactions", tables)

    def test_action_packet_is_json_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "workspace"
            ensure_project(project)
            initialize_database(project, sample=True)
            initialize_wallet(project, 50000)
            packet = build_action_packet(project)
            encoded = json.dumps(packet)
            self.assertIn("research_only", encoded)


if __name__ == "__main__":
    unittest.main()
