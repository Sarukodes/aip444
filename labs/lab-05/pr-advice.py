import os
import re
import sys
import json
import requests

from dotenv import load_dotenv
from openai import OpenAI
from tools import read_github_files

MAX_DIFF_SIZE = 95000


def load_env():
    load_dotenv()
    load_dotenv("../../.env")


def parse_pr_url(url):
    pattern = r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)$"
    match = re.match(pattern, url)

    if not match:
        print("Error: Please provide a valid GitHub PR URL.")
        sys.exit(1)

    return match.group(1), match.group(2), match.group(3)


def fetch_patch(url):
    patch_url = url + ".patch"
    response = requests.get(patch_url)

    if response.status_code != 200:
        raise Exception(f"Unable to fetch patch: {response.status_code}")

    patch = response.text

    if len(patch) > MAX_DIFF_SIZE:
        print("Warning: Patch is too large and was truncated.")
        patch = patch[:MAX_DIFF_SIZE] + "\n\n...[Diff Truncated]..."

    return patch


def fetch_comments(owner, repo, number):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"

    headers = {
        "User-Agent": "AIP444-Lab-05",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitHub API Error: {response.status_code}")

    return [
        {
            "username": item["user"]["login"],
            "body": item["body"],
            "date": item["updated_at"],
        }
        for item in response.json()
    ]


def build_thread(comments):
    thread = "<thread>\n"

    for comment in comments:
        thread += (
            f'<comment username="{comment["username"]}" '
            f'date="{comment["date"]}">\n'
            f'{comment["body"]}\n'
            f'</comment>\n'
        )

    thread += "</thread>"
    return thread


def load_system_prompt():
    with open("SYSTEM_PROMPT.md", "r", encoding="utf-8") as file:
        return file.read()


def build_user_prompt(pr_url, owner, repo, patch, thread):
    return f"""
## PR URL

{pr_url}

## REPOSITORY

Owner: {owner}
Repo: {repo}
Ref: main

## DIFF

```diff
{patch}
```

## COMMENTS

{thread}
"""


def generate_report(system_prompt, user_prompt):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("Error: OPENROUTER_API_KEY is missing in .env file.")
        sys.exit(1)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_github_files",
                "description": (
                    "Read one or more files from GitHub when the PR diff "
                    "does not provide enough context."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "description": "GitHub files to read.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "owner": {"type": "string"},
                                    "repo": {"type": "string"},
                                    "path": {"type": "string"},
                                    "ref": {"type": "string"},
                                },
                                "required": ["owner", "repo", "path", "ref"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["files"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    max_iterations = 5

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=messages,
            tools=tools,
        )

        assistant_message = response.choices[0].message

        if not assistant_message.tool_calls:
            return assistant_message.content

        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            args = json.loads(tool_call.function.arguments)

            print(f"\nTool called: {tool_call.function.name}")
            print(f"Arguments: {args}\n")

            if tool_call.function.name == "read_github_files":
                result = read_github_files(args["files"])
            else:
                result = f"Unknown tool: {tool_call.function.name}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return "Max tool-calling iterations reached."


def main():
    load_env()

    if len(sys.argv) != 2:
        print("Usage: python pr-advice.py <github-pr-url>")
        sys.exit(1)

    pr_url = sys.argv[1]

    owner, repo, number = parse_pr_url(pr_url)
    patch = fetch_patch(pr_url)
    comments = fetch_comments(owner, repo, number)
    thread = build_thread(comments)

    system_prompt = load_system_prompt()
    user_prompt = build_user_prompt(pr_url, owner, repo, patch, thread)

    report = generate_report(system_prompt, user_prompt)

    print(report)


if __name__ == "__main__":
    main()