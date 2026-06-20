import os
import subprocess
from pathlib import Path


MAX_FILE_LINES = 300
MAX_RG_RESULTS = 80
MAX_OUTPUT_CHARS = 12000


def is_inside(child: Path, parent: Path) -> bool:
    """
    Checks if child path is inside parent path.
    """
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def get_repo_root() -> Path:
    """
    Finds the git repo root by walking upward until .git is found.
    If no .git folder is found, uses the current directory.
    """
    current = Path.cwd().resolve()

    for path in [current, *current.parents]:
        if (path / ".git").exists():
            return path

    return current


def safe_path(file_path: str) -> Path:
    """
    Converts a user/model-provided path into a safe local path.
    Allows paths inside the current folder or repo root only.
    """
    cwd = Path.cwd().resolve()
    repo_root = get_repo_root().resolve()

    raw_path = Path(file_path)

    if raw_path.is_absolute():
        target_path = raw_path.resolve()
    else:
        cwd_candidate = (cwd / raw_path).resolve()
        repo_candidate = (repo_root / raw_path).resolve()

        if cwd_candidate.exists():
            target_path = cwd_candidate
        else:
            target_path = repo_candidate

    if not (is_inside(target_path, cwd) or is_inside(target_path, repo_root)):
        raise ValueError("Access denied: file path is outside the project folder.")

    return target_path


def read_file(file_path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    """
    Reads a file from disk, optionally between start_line and end_line.
    Line numbers are 1-based.
    """
    try:
        path = safe_path(file_path)

        if not path.exists():
            return f"ERROR: File not found: {file_path}"

        if not path.is_file():
            return f"ERROR: Path is not a file: {file_path}"

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)

        if start_line is None:
            start_line = 1

        if end_line is None:
            end_line = min(total_lines, MAX_FILE_LINES)

        start_line = max(1, start_line)
        end_line = min(total_lines, end_line)

        selected_lines = lines[start_line - 1:end_line]

        numbered_output = []
        for line_number, line in enumerate(selected_lines, start=start_line):
            numbered_output.append(f"{line_number}: {line.rstrip()}")

        result = "\n".join(numbered_output)

        if total_lines > end_line:
            result += f"\n\n[TRUNCATED: showing lines {start_line}-{end_line} of {total_lines}]"

        return result

    except Exception as e:
        return f"ERROR reading file {file_path}: {e}"


def ripgrep(search_pattern: str) -> str:
    """
    Searches the project folder for a pattern.

    First tries real ripgrep command 'rg'.
    If rg is not available, falls back to a Python recursive search.
    """
    try:
        command = [
            "rg",
            "--line-number",
            "--hidden",
            "--glob",
            "!.git",
            "--glob",
            "!.env",
            search_pattern,
            ".",
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )

        if result.returncode == 1:
            return f"No matches found for pattern: {search_pattern}"

        if result.returncode == 0:
            output_lines = result.stdout.splitlines()

            if len(output_lines) > MAX_RG_RESULTS:
                output_lines = output_lines[:MAX_RG_RESULTS]
                output_lines.append(f"[TRUNCATED: showing first {MAX_RG_RESULTS} matches]")

            output = "\n".join(output_lines)

            if len(output) > MAX_OUTPUT_CHARS:
                output = output[:MAX_OUTPUT_CHARS] + "\n[TRUNCATED: output too long]"

            return output

    except FileNotFoundError:
        pass

    except Exception:
        pass

    # Backup search if rg is not installed or not available in PATH
    matches = []
    search_root = Path.cwd().resolve()

    skip_dirs = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
    }

    skip_files = {
        ".env",
    }

    for root, dirs, files in os.walk(search_root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file_name in files:
            if file_name in skip_files:
                continue

            file_path = Path(root) / file_name

            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    for line_number, line in enumerate(f, start=1):
                        if search_pattern.lower() in line.lower():
                            relative_path = file_path.relative_to(search_root)
                            matches.append(f"./{relative_path.as_posix()}:{line_number}: {line.rstrip()}")

                            if len(matches) >= MAX_RG_RESULTS:
                                matches.append(f"[TRUNCATED: showing first {MAX_RG_RESULTS} matches]")
                                return "\n".join(matches)

            except Exception:
                continue

    if not matches:
        return f"No matches found for pattern: {search_pattern}"

    output = "\n".join(matches)

    if len(output) > MAX_OUTPUT_CHARS:
        output = output[:MAX_OUTPUT_CHARS] + "\n[TRUNCATED: output too long]"

    return output


TOOL_FUNCTIONS = {
    "read_file": read_file,
    "ripgrep": ripgrep,
}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a source file from disk. Optionally provide start_line and end_line using 1-based line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path of the file to read, relative to the current folder or repo root.",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Optional starting line number, 1-based.",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Optional ending line number, 1-based.",
                    },
                },
                "required": ["file_path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ripgrep",
            "description": "Search the project recursively for a text pattern and return matching file paths, line numbers, and lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_pattern": {
                        "type": "string",
                        "description": "The text or pattern to search for in the project.",
                    },
                },
                "required": ["search_pattern"],
                "additionalProperties": False,
            },
        },
    },
]