# tools.py

import requests

MAX_LINES = 1000


def read_github_files(files):
    results = []

    for file in files:
        owner = file["owner"]
        repo = file["repo"]
        path = file["path"]
        ref = file.get("ref", "main")

        url = (
            f"https://raw.githubusercontent.com/"
            f"{owner}/{repo}/refs/heads/{ref}/{path}"
        )

        try:
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                results.append(
                    f"# {path}\nERROR: HTTP {response.status_code}"
                )
                continue

            content = response.text

            lines = content.splitlines()

            total_lines = len(lines)

            if total_lines > MAX_LINES:
                content = "\n".join(lines[:MAX_LINES])
                content += (
                    f"\n\n[File truncated: showing first "
                    f"{MAX_LINES} of {total_lines} lines]"
                )

            results.append(
                f"# File: {path}\n\n```text\n{content}\n```"
            )

        except Exception as e:
            results.append(
                f"# {path}\nERROR: {str(e)}"
            )

    return "\n\n---\n\n".join(results)