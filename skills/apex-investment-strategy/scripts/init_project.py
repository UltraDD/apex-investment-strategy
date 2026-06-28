from __future__ import annotations

import argparse
import sys

from apexlib import ensure_project, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a local Apex investment strategy workspace.")
    parser.add_argument("--project-dir", required=True, help="Target local workspace directory.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite generated config and README files.")
    parser.add_argument(
        "--profile",
        choices=["minimal", "apex17"],
        default="minimal",
        help="Workspace profile: minimal demo config or public Apex-aligned 17-asset config.",
    )
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        root = ensure_project(parsed.project_dir, overwrite=parsed.overwrite, profile=parsed.profile)
        return {"project_dir": str(root), "status": "initialized", "profile": parsed.profile}

    return run_cli(command, args)


if __name__ == "__main__":
    sys.exit(main())
