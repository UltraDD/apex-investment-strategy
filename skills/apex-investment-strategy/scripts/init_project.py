from __future__ import annotations

import argparse
import sys

from apexlib import ensure_project, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a local Apex investment strategy workspace.")
    parser.add_argument("--project-dir", required=True, help="Target local workspace directory.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite generated config and README files.")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        root = ensure_project(parsed.project_dir, overwrite=parsed.overwrite)
        return {"project_dir": str(root), "status": "initialized"}

    return run_cli(command, args)


if __name__ == "__main__":
    sys.exit(main())

