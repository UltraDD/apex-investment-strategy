from __future__ import annotations

import argparse
import sys

from apexlib import initialize_database, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the local SQLite database and optionally import data.")
    parser.add_argument("--project-dir", required=True, help="Local Apex workspace directory.")
    parser.add_argument("--csv", help="Optional price CSV to import.")
    parser.add_argument("--sample", action="store_true", help="Generate and import deterministic sample data.")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return initialize_database(parsed.project_dir, sample=parsed.sample, csv_file=parsed.csv)

    return run_cli(command, args)


if __name__ == "__main__":
    sys.exit(main())

