from __future__ import annotations

import argparse
import sys

from apexlib import initialize_wallet, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a local paper wallet.")
    parser.add_argument("--project-dir", required=True, help="Local Apex workspace directory.")
    parser.add_argument("--capital", required=True, type=float, help="Starting paper capital.")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return initialize_wallet(parsed.project_dir, parsed.capital)

    return run_cli(command, args)


if __name__ == "__main__":
    sys.exit(main())

