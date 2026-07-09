from __future__ import annotations

import argparse
import sys

from apexlib import generate_ai_research_brief, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="基于本地 Apex 报告生成 AI 研究解读。")
    parser.add_argument("--project-dir", required=True, help="Apex 本地研究工作区目录。")
    parser.add_argument("--base-url", help="OpenAI 兼容接口地址，默认读取环境变量或 OpenAI 地址。")
    parser.add_argument("--model", help="聊天模型名称，默认读取 APEX_AI_MODEL、OPENAI_MODEL 或工具默认值。")
    parser.add_argument("--timeout", type=float, default=30.0, help="请求超时时间，单位秒。")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return generate_ai_research_brief(
            parsed.project_dir,
            base_url=parsed.base_url,
            model=parsed.model,
            timeout=parsed.timeout,
        )

    return run_cli(command, args, title="生成 AI 研究解读")


if __name__ == "__main__":
    sys.exit(main())
