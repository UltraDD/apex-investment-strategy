from __future__ import annotations

import argparse
import sys

from apexlib import run_cli, validate_data


def main() -> int:
    parser = argparse.ArgumentParser(description="校验本地价格数据库覆盖情况。")
    parser.add_argument("--project-dir", required=True, help="Apex 本地研究工作区目录。")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return validate_data(parsed.project_dir)

    return run_cli(command, args, title="校验行情数据覆盖情况")


if __name__ == "__main__":
    sys.exit(main())
