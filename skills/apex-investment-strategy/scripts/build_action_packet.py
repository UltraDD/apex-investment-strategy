from __future__ import annotations

import argparse
import sys

from apexlib import build_action_packet, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="生成本地研究行动建议包（不连接券商）。")
    parser.add_argument("--project-dir", required=True, help="Apex 本地研究工作区目录。")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return build_action_packet(parsed.project_dir)

    return run_cli(command, args, title="生成行动建议包")


if __name__ == "__main__":
    sys.exit(main())
