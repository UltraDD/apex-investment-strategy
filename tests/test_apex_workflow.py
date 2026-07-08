from __future__ import annotations

import csv
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "apex-investment-strategy" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from apexlib import (  # noqa: E402
    build_action_packet,
    ensure_project,
    generate_ai_research_brief,
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
            self.assertIn("Apex 资产动量研究与AI解读工具", html)
            self.assertNotIn("__ACTION_JSON__", html)

    def test_apex17_profile_scaffolds_public_alignment_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "workspace"

            ensure_project(project, profile="apex17")
            config = json.loads((project / "config.json").read_text(encoding="utf-8"))
            tradable_assets = [asset["id"] for asset in config["assets"] if asset["id"] != "cash"]

            self.assertEqual(len(tradable_assets), 17)
            self.assertIn("semiconductor", tradable_assets)
            self.assertEqual(config["strategy"]["lookback_days"], 252)

            init_result = initialize_database(project, sample=True)
            self.assertEqual(init_result["imported_rows"], 17 * 560)

            health = validate_data(project)
            self.assertTrue(health["ok"])
            self.assertEqual(len(health["assets"]), 17)

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

    def test_ai_research_brief_is_written_and_embedded_in_web_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "workspace"
            ensure_project(project)
            initialize_database(project, sample=True)
            run_backtest(project)
            build_action_packet(project)

            with (
                patch.dict(os.environ, {"APEX_AI_API_KEY": "test-key"}),
                patch("apexlib.call_openai_compatible_chat", return_value="本期信号来自本地研究文件，应先核对数据覆盖情况。"),
            ):
                result = generate_ai_research_brief(project, model="test-model")
            self.assertEqual(result["status"], "ai_generated")
            brief_json = json.loads((project / "reports" / "ai-brief.json").read_text(encoding="utf-8"))
            self.assertEqual(brief_json["model"], "test-model")
            self.assertIn("数据覆盖", brief_json["brief_markdown"])

            web = scaffold_web(project)
            html = Path(web["web_index"]).read_text(encoding="utf-8")
            self.assertIn("AI 研究解读", html)
            self.assertIn("本期信号来自本地研究文件", html)


if __name__ == "__main__":
    unittest.main()
