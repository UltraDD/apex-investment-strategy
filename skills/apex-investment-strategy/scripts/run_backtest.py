from __future__ import annotations

import argparse
import sys

from apexlib import run_backtest, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="运行公开资产动量研究回测。")
    parser.add_argument("--project-dir", required=True, help="Apex 本地研究工作区目录。")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return run_backtest(parsed.project_dir)

    return run_cli(command, args, title="运行资产动量研究回测")


if __name__ == "__main__":
    sys.exit(main())
