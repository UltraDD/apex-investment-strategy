from __future__ import annotations

import argparse
import sys

from apexlib import (
    build_action_packet,
    ensure_project,
    generate_ai_research_brief,
    initialize_database,
    initialize_wallet,
    run_backtest,
    run_cli,
    scaffold_web,
    validate_data,
)


def add_workspace_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace",
        "--project-dir",
        dest="project_dir",
        required=True,
        help="Apex 本地研究工作区目录。",
    )


def command_init(args: argparse.Namespace) -> int:
    def command(parsed: argparse.Namespace) -> dict[str, object]:
        root = ensure_project(parsed.project_dir, overwrite=parsed.overwrite, profile=parsed.profile)
        return {"project_dir": str(root), "status": "initialized", "status_label": "已初始化", "profile": parsed.profile}

    return run_cli(command, args, title="初始化本地研究工作区")


def command_import(args: argparse.Namespace) -> int:
    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return initialize_database(parsed.project_dir, sample=parsed.sample, csv_file=parsed.csv)

    return run_cli(command, args, title="创建数据库并导入行情数据")


def command_validate(args: argparse.Namespace) -> int:
    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return validate_data(parsed.project_dir)

    return run_cli(command, args, title="校验行情数据覆盖情况")


def command_backtest(args: argparse.Namespace) -> int:
    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return run_backtest(parsed.project_dir)

    return run_cli(command, args, title="运行资产动量研究回测")


def command_wallet(args: argparse.Namespace) -> int:
    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return initialize_wallet(parsed.project_dir, parsed.capital)

    return run_cli(command, args, title="初始化纸面钱包")


def command_packet(args: argparse.Namespace) -> int:
    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return build_action_packet(parsed.project_dir)

    return run_cli(command, args, title="生成行动建议包")


def command_explain(args: argparse.Namespace) -> int:
    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return generate_ai_research_brief(
            parsed.project_dir,
            base_url=parsed.base_url,
            model=parsed.model,
            timeout=parsed.timeout,
        )

    return run_cli(command, args, title="生成 AI 研究解读")


def command_web(args: argparse.Namespace) -> int:
    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return scaffold_web(parsed.project_dir)

    return run_cli(command, args, title="生成静态网页报告")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apex资产动量研究与AI解读软件命令入口。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="初始化本地研究工作区。")
    add_workspace_argument(init_parser)
    init_parser.add_argument("--overwrite", action="store_true", help="覆盖已生成的配置和 README 文件。")
    init_parser.add_argument(
        "--profile",
        choices=["minimal", "apex17"],
        default="minimal",
        help="工作区画像：minimal 演示配置，或 apex17 公开 17 标的配置。",
    )
    init_parser.set_defaults(handler=command_init)

    import_parser = subparsers.add_parser("import", help="创建数据库并导入行情数据。")
    add_workspace_argument(import_parser)
    import_parser.add_argument("--csv", help="要导入的价格 CSV 文件。")
    import_parser.add_argument("--sample", action="store_true", help="生成并导入流程演示用示例数据。")
    import_parser.set_defaults(handler=command_import)

    validate_parser = subparsers.add_parser("validate", help="校验行情数据覆盖情况。")
    add_workspace_argument(validate_parser)
    validate_parser.set_defaults(handler=command_validate)

    backtest_parser = subparsers.add_parser("backtest", help="运行资产动量研究回测。")
    add_workspace_argument(backtest_parser)
    backtest_parser.set_defaults(handler=command_backtest)

    wallet_parser = subparsers.add_parser("wallet", help="初始化本地纸面钱包。")
    add_workspace_argument(wallet_parser)
    wallet_parser.add_argument("--capital", required=True, type=float, help="纸面钱包初始资金。")
    wallet_parser.set_defaults(handler=command_wallet)

    packet_parser = subparsers.add_parser("packet", help="生成本地研究行动建议包。")
    add_workspace_argument(packet_parser)
    packet_parser.set_defaults(handler=command_packet)

    explain_parser = subparsers.add_parser("explain", help="基于本地报告生成 AI 研究解读。")
    add_workspace_argument(explain_parser)
    explain_parser.add_argument("--base-url", help="OpenAI 兼容接口地址，默认读取环境变量或 OpenAI 地址。")
    explain_parser.add_argument("--model", help="聊天模型名称，默认读取环境变量或工具默认值。")
    explain_parser.add_argument("--timeout", type=float, default=30.0, help="请求超时时间，单位秒。")
    explain_parser.set_defaults(handler=command_explain)

    web_parser = subparsers.add_parser("web", help="生成本地静态网页报告。")
    add_workspace_argument(web_parser)
    web_parser.set_defaults(handler=command_web)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
