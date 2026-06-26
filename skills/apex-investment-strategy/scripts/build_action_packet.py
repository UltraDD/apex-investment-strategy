from __future__ import annotations

import argparse
import sys

from apexlib import build_action_packet, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the local research Action Packet.")
    parser.add_argument("--project-dir", required=True, help="Local Apex workspace directory.")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return build_action_packet(parsed.project_dir)

    return run_cli(command, args)


if __name__ == "__main__":
    sys.exit(main())

