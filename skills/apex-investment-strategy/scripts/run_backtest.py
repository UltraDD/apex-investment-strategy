from __future__ import annotations

import argparse
import sys

from apexlib import run_backtest, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the public research backtest.")
    parser.add_argument("--project-dir", required=True, help="Local Apex workspace directory.")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return run_backtest(parsed.project_dir)

    return run_cli(command, args)


if __name__ == "__main__":
    sys.exit(main())

