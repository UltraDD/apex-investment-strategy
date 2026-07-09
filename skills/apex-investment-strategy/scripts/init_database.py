from __future__ import annotations

import argparse
import sys

from apexlib import initialize_database, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="创建本地 SQLite 研究数据库，并按需导入价格数据。")
    parser.add_argument("--project-dir", required=True, help="Apex 本地研究工作区目录。")
    parser.add_argument("--csv", help="要导入的价格 CSV 文件。")
    parser.add_argument("--sample", action="store_true", help="生成并导入流程演示用示例数据。")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return initialize_database(parsed.project_dir, sample=parsed.sample, csv_file=parsed.csv)

    return run_cli(command, args, title="创建数据库并导入行情数据")


if __name__ == "__main__":
    sys.exit(main())
