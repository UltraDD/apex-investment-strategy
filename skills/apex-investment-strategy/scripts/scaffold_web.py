from __future__ import annotations

import argparse
import sys

from apexlib import run_cli, scaffold_web


def main() -> int:
    parser = argparse.ArgumentParser(description="生成本地 Apex 静态网页报告。")
    parser.add_argument("--project-dir", required=True, help="Apex 本地研究工作区目录。")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return scaffold_web(parsed.project_dir)

    return run_cli(command, args, title="生成静态网页报告")


if __name__ == "__main__":
    sys.exit(main())
