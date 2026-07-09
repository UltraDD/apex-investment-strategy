from __future__ import annotations

import argparse
import sys

from apexlib import initialize_wallet, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化本地纸面钱包。")
    parser.add_argument("--project-dir", required=True, help="Apex 本地研究工作区目录。")
    parser.add_argument("--capital", required=True, type=float, help="纸面钱包初始资金。")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return initialize_wallet(parsed.project_dir, parsed.capital)

    return run_cli(command, args, title="初始化纸面钱包")


if __name__ == "__main__":
    sys.exit(main())
