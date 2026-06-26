from __future__ import annotations

import argparse
import sys

from apexlib import run_cli, validate_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local price database coverage.")
    parser.add_argument("--project-dir", required=True, help="Local Apex workspace directory.")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return validate_data(parsed.project_dir)

    return run_cli(command, args)


if __name__ == "__main__":
    sys.exit(main())

