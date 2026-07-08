from __future__ import annotations

import argparse
import sys

from apexlib import generate_ai_research_brief, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an AI research brief from local Apex reports.")
    parser.add_argument("--project-dir", required=True, help="Local Apex workspace directory.")
    parser.add_argument("--base-url", help="OpenAI-compatible API base URL. Defaults to env or OpenAI.")
    parser.add_argument("--model", help="Chat model name. Defaults to APEX_AI_MODEL, OPENAI_MODEL, or tool default.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds.")
    args = parser.parse_args()

    def command(parsed: argparse.Namespace) -> dict[str, object]:
        return generate_ai_research_brief(
            parsed.project_dir,
            base_url=parsed.base_url,
            model=parsed.model,
            timeout=parsed.timeout,
        )

    return run_cli(command, args)


if __name__ == "__main__":
    sys.exit(main())
