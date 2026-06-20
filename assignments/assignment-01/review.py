import argparse
import asyncio
import html
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI

from prompts import (
    LEAD_DEVELOPER_PROMPT,
    MAINTAINABILITY_CRITIC_PROMPT,
    SECURITY_AUDITOR_PROMPT,
)
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS, read_file


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

DEFAULT_REVIEWER_MODEL = "google/gemini-2.5-flash-lite"
DEFAULT_JUDGE_MODEL = "google/gemini-2.5-flash-lite"

MAX_TOOL_ITERATIONS = 5
MAX_INPUT_CHARS = 30000
MAX_TOOL_OUTPUT_LOG_CHARS = 2500


def debug_log(debug: bool, message: str) -> None:
    """
    Debug logs must go to stderr.
    Final user output should go to stdout.
    """
    if debug:
        print(message, file=sys.stderr)


def truncate_text(text: str, max_chars: int) -> str:
    """
    Keeps prompts and debug output from becoming too large.
    """
    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "\n\n[TRUNCATED: input was too large]"


def load_api_key() -> str:
    """
    Loads OpenRouter API key from .env.
    """
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print(
            "ERROR: OPENROUTER_API_KEY was not found. Add it to your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    return api_key


def get_default_output_filename() -> str:
    """
    Creates default filename like review-DD-MM-YYYY-HH-MM-SS.html.
    """
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    return f"review-{timestamp}.html"


def get_staged_diff() -> str:
    """
    Reads staged git changes using git diff --staged.
    """
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        print(f"ERROR running git diff --staged: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    return result.stdout.strip()


def get_input(args: argparse.Namespace) -> tuple[str, str]:
    """
    Returns review mode and input text.
    Mode can be FILE or GIT.
    """
    if args.file:
        content = read_file(args.file)

        if content.startswith("ERROR:"):
            print(content, file=sys.stderr)
            sys.exit(1)

        review_input = f"""
FILE MODE REVIEW

File path:
{args.file}

File content with line numbers:
{content}
"""
        return "FILE", truncate_text(review_input.strip(), MAX_INPUT_CHARS)

    diff = get_staged_diff()

    if not diff:
        print(
            "No staged changes found. Use --file filename or stage files with git add.",
            file=sys.stderr,
        )
        sys.exit(1)

    review_input = f"""
GIT MODE REVIEW

The following is the staged git diff from git diff --staged:

{diff}
"""
    return "GIT", truncate_text(review_input.strip(), MAX_INPUT_CHARS)


def extract_file_path_from_review_input(review_input: str) -> str | None:
    """
    Extracts the file path from File Mode input.
    Returns None for Git Mode.
    """
    marker = "File path:"

    if marker not in review_input:
        return None

    after_marker = review_input.split(marker, 1)[1].strip()

    if not after_marker:
        return None

    return after_marker.splitlines()[0].strip()


def parse_json_findings(raw_text: str) -> list[dict[str, Any]]:
    """
    Parses reviewer JSON.
    Accepts either:
    - a JSON array: [...]
    - an object with findings: {"findings": [...]}
    """
    text = raw_text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start_array = text.find("[")
        end_array = text.rfind("]")

        if start_array != -1 and end_array != -1 and end_array > start_array:
            data = json.loads(text[start_array : end_array + 1])
        else:
            return [
                {
                    "path": "unknown",
                    "line": 0,
                    "severity": "warn",
                    "category": "tooling",
                    "description": "Reviewer returned text that could not be parsed as JSON.",
                }
            ]

    if isinstance(data, dict) and "findings" in data:
        data = data["findings"]

    if not isinstance(data, list):
        return [
            {
                "path": "unknown",
                "line": 0,
                "severity": "warn",
                "category": "tooling",
                "description": "Reviewer output was JSON but not a list of findings.",
            }
        ]

    valid_findings = []

    for item in data:
        if not isinstance(item, dict):
            continue

        valid_findings.append(
            {
                "path": str(item.get("path", "unknown")),
                "line": int(item.get("line", 0) or 0),
                "severity": str(item.get("severity", "info")),
                "category": str(item.get("category", "general")),
                "description": str(item.get("description", "")),
            }
        )

    return valid_findings


async def call_llm_with_retries(
    client: AsyncOpenAI,
    *,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | None = None,
    max_retries: int = 3,
) -> Any:
    """
    Calls the model with small retry logic for temporary failures/rate limits.
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }

            if tools is not None:
                kwargs["tools"] = tools

            if tool_choice is not None:
                kwargs["tool_choice"] = tool_choice

            return await client.chat.completions.create(**kwargs)

        except Exception as e:
            last_error = e
            wait_time = 2**attempt
            await asyncio.sleep(wait_time)

    raise RuntimeError(f"LLM call failed after retries: {last_error}")


def run_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """
    Runs a local Python tool requested by the LLM.
    """
    if tool_name not in TOOL_FUNCTIONS:
        return f"ERROR: Unknown tool requested: {tool_name}"

    try:
        tool_func = TOOL_FUNCTIONS[tool_name]
        return tool_func(**arguments)
    except Exception as e:
        return f"ERROR running tool {tool_name}: {e}"


async def run_reviewer(
    client: AsyncOpenAI,
    *,
    reviewer_name: str,
    system_prompt: str,
    review_input: str,
    temperature: float,
    debug: bool,
) -> list[dict[str, Any]]:
    """
    Runs one reviewer agent.
    The reviewer gets tool context, can call more tools, then returns JSON findings.
    """
    reviewer_model = os.getenv("REVIEWER_MODEL", DEFAULT_REVIEWER_MODEL)

    debug_log(debug, f"[{reviewer_name}] Started using model: {reviewer_model}")

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": f"""
Review this input.

Important:
- You may call tools if you need more context.
- After tool use is complete, return only the final JSON array of findings.
- Do not include markdown or extra explanation.

Input:
{review_input}
""".strip(),
        },
    ]

    # Required tool context so debug mode clearly proves tools are being used.
    pre_tool_name = None
    pre_tool_args = None

    if reviewer_name == "Security Auditor":
        pre_tool_name = "ripgrep"
        pre_tool_args = {"search_pattern": "api_key"}

    elif reviewer_name == "Maintainability Critic":
        file_path = extract_file_path_from_review_input(review_input)

        if file_path:
            pre_tool_name = "read_file"
            pre_tool_args = {"file_path": file_path}
        else:
            pre_tool_name = "ripgrep"
            pre_tool_args = {"search_pattern": "import"}

    if pre_tool_name and pre_tool_args:
        debug_log(
            debug,
            f"[{reviewer_name}] Calling tool {pre_tool_name} with arguments: "
            f"{json.dumps(pre_tool_args, indent=2)}",
        )

        pre_tool_output = run_tool(pre_tool_name, pre_tool_args)

        debug_log(
            debug,
            f"[Tool:{pre_tool_name}] Output:\n"
            f"{truncate_text(pre_tool_output, MAX_TOOL_OUTPUT_LOG_CHARS)}",
        )

        messages.append(
            {
                "role": "user",
                "content": f"""
Pre-review tool context gathered from {pre_tool_name}.

Tool arguments:
{json.dumps(pre_tool_args, indent=2)}

Tool output:
{pre_tool_output}

Use this tool context when producing your final JSON findings.
""".strip(),
            }
        )

    for iteration in range(MAX_TOOL_ITERATIONS):
        debug_log(debug, f"[{reviewer_name}] LLM iteration {iteration + 1}")

        response = await call_llm_with_retries(
            client,
            model=reviewer_model,
            messages=messages,
            temperature=temperature,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)

        if tool_calls:
            messages.append(message.model_dump(exclude_none=True))

            for tool_call in tool_calls:
                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}

                debug_log(
                    debug,
                    f"[{reviewer_name}] Calling tool {tool_name} with arguments: "
                    f"{json.dumps(arguments, indent=2)}",
                )

                tool_output = run_tool(tool_name, arguments)

                debug_log(
                    debug,
                    f"[Tool:{tool_name}] Output:\n"
                    f"{truncate_text(tool_output, MAX_TOOL_OUTPUT_LOG_CHARS)}",
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_output,
                    }
                )

            continue

        raw_content = message.content or "[]"

        debug_log(debug, f"[{reviewer_name}] Raw JSON response:\n{raw_content}")

        findings = parse_json_findings(raw_content)

        debug_log(
            debug,
            f"[{reviewer_name}] Parsed findings:\n{json.dumps(findings, indent=2)}",
        )

        debug_log(debug, f"[{reviewer_name}] Finished with {len(findings)} finding(s)")

        return findings

    debug_log(
        debug,
        f"[{reviewer_name}] Tool loop reached max iterations. Forcing final JSON response.",
    )

    messages.append(
        {
            "role": "user",
            "content": "Stop calling tools. Return only the final JSON array of findings now.",
        }
    )

    response = await call_llm_with_retries(
        client,
        model=reviewer_model,
        messages=messages,
        temperature=temperature,
    )

    raw_content = response.choices[0].message.content or "[]"

    debug_log(debug, f"[{reviewer_name}] Forced raw JSON response:\n{raw_content}")

    findings = parse_json_findings(raw_content)

    debug_log(debug, f"[{reviewer_name}] Finished with {len(findings)} finding(s)")

    return findings


def fallback_html_report(
    security_findings: list[dict[str, Any]],
    maintainability_findings: list[dict[str, Any]],
) -> str:
    """
    Creates a fallback HTML report if the judge response is not valid HTML.
    """
    all_findings = security_findings + maintainability_findings

    rows = []

    for finding in all_findings:
        rows.append(
            f"""
            <tr>
                <td>{html.escape(str(finding.get("severity", "")))}</td>
                <td>{html.escape(str(finding.get("category", "")))}</td>
                <td>{html.escape(str(finding.get("path", "")))}:{html.escape(str(finding.get("line", "")))}</td>
                <td>{html.escape(str(finding.get("description", "")))}</td>
            </tr>
            """
        )

    rows_html = "\n".join(rows) if rows else """
        <tr>
            <td colspan="4">No major issues found.</td>
        </tr>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Code Review Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #f5f7fb;
            color: #1f2937;
            padding: 40px;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: white;
            padding: 32px;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.08);
        }}
        h1 {{
            margin-top: 0;
        }}
        .summary {{
            background: #eef2ff;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 24px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
            vertical-align: top;
        }}
        th {{
            background: #f9fafb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Code Review Report</h1>
        <div class="summary">
            <strong>Total findings:</strong> {len(all_findings)}
        </div>
        <table>
            <thead>
                <tr>
                    <th>Severity</th>
                    <th>Category</th>
                    <th>Location</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""


async def run_judge(
    client: AsyncOpenAI,
    *,
    review_input: str,
    security_findings: list[dict[str, Any]],
    maintainability_findings: list[dict[str, Any]],
    debug: bool,
) -> str:
    """
    Runs the Lead Developer/Judge model to create final HTML report.
    """
    judge_model = os.getenv("JUDGE_MODEL", DEFAULT_JUDGE_MODEL)

    debug_log(debug, f"[Lead Developer] Started using model: {judge_model}")

    judge_payload = {
        "review_input_summary": truncate_text(review_input, 8000),
        "security_auditor_findings": security_findings,
        "maintainability_critic_findings": maintainability_findings,
    }

    messages = [
        {
            "role": "system",
            "content": LEAD_DEVELOPER_PROMPT,
        },
        {
            "role": "user",
            "content": json.dumps(judge_payload, indent=2),
        },
    ]

    response = await call_llm_with_retries(
        client,
        model=judge_model,
        messages=messages,
        temperature=0.3,
    )

    html_report = response.choices[0].message.content or ""

    debug_log(debug, f"[Lead Developer] Raw HTML response length: {len(html_report)}")
    debug_log(debug, "[Lead Developer] Finished")

    if "<html" not in html_report.lower():
        debug_log(
            debug,
            "[Lead Developer] Response did not look like HTML. Using fallback HTML report.",
        )
        return fallback_html_report(security_findings, maintainability_findings)

    return html_report


async def main_async() -> None:
    parser = argparse.ArgumentParser(
        description="AI Code Review CLI using two reviewers and a Lead Developer judge."
    )

    parser.add_argument(
        "--file",
        help="Review a specific file instead of staged git changes.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print detailed debug logs to stderr.",
    )

    parser.add_argument(
        "--output",
        help="Output HTML report filename.",
    )

    args = parser.parse_args()

    api_key = load_api_key()

    client = AsyncOpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )

    mode, review_input = get_input(args)

    debug_log(args.debug, f"[Main] Mode: {mode}")
    debug_log(args.debug, f"[Main] Review input length: {len(review_input)} characters")
    debug_log(args.debug, "[Main] Starting parallel reviewers")

    start_time = time.time()

    security_task = run_reviewer(
        client,
        reviewer_name="Security Auditor",
        system_prompt=SECURITY_AUDITOR_PROMPT,
        review_input=review_input,
        temperature=0.1,
        debug=args.debug,
    )

    maintainability_task = run_reviewer(
        client,
        reviewer_name="Maintainability Critic",
        system_prompt=MAINTAINABILITY_CRITIC_PROMPT,
        review_input=review_input,
        temperature=0.3,
        debug=args.debug,
    )

    security_findings, maintainability_findings = await asyncio.gather(
        security_task,
        maintainability_task,
    )

    debug_log(args.debug, "[Main] Parallel reviewers finished")

    debug_log(
        args.debug,
        "[Main] Security Auditor raw findings:\n"
        + json.dumps(security_findings, indent=2),
    )

    debug_log(
        args.debug,
        "[Main] Maintainability Critic raw findings:\n"
        + json.dumps(maintainability_findings, indent=2),
    )

    debug_log(args.debug, "[Main] Starting Lead Developer synthesis")

    html_report = await run_judge(
        client,
        review_input=review_input,
        security_findings=security_findings,
        maintainability_findings=maintainability_findings,
        debug=args.debug,
    )

    output_file = args.output or get_default_output_filename()
    output_path = Path(output_file)

    output_path.write_text(html_report, encoding="utf-8")

    elapsed = time.time() - start_time

    debug_log(args.debug, f"[Main] Report written to {output_path}")
    debug_log(args.debug, f"[Main] Total runtime: {elapsed:.2f} seconds")

    print(f"Saved HTML report to {output_path}")


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()