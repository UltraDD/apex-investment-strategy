from __future__ import annotations

import argparse
import sys

from apexlib import ensure_project, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 Apex 本地资产动量研究工作区。")
    parser.add_argument("--project-dir", required=True, help="目标本地工作区目录。")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已生成的配置和 README 文件。")
    parser.add_argument(
        "--profile",
        choices=["minimal", "apex17"],
        default="minimal",
        help="工作区画像：minimal 演示配置，或 apex17 公开 17 标的配置。",
    )
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        root = ensure_project(parsed.project_dir, overwrite=parsed.overwrite, profile=parsed.profile)
        return {"project_dir": str(root), "status": "initialized", "status_label": "已初始化", "profile": parsed.profile}

    return run_cli(command, args, title="初始化本地研究工作区")


if __name__ == "__main__":
    sys.exit(main())
