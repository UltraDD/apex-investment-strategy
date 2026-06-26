from __future__ import annotations

import argparse
import sys

from apexlib import run_cli, scaffold_web


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a static local Apex web dashboard.")
    parser.add_argument("--project-dir", required=True, help="Local Apex workspace directory.")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return scaffold_web(parsed.project_dir)

    return run_cli(command, args)


if __name__ == "__main__":
    sys.exit(main())

