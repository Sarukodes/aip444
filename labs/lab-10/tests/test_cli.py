"""Tests for the command-line Data URI encoder."""

import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = Path(__file__).parent / "fixtures"
CLI_PATH = PROJECT_ROOT / "src" / "cli.py"


def run_cli(*arguments: str | Path) -> subprocess.CompletedProcess[str]:
    """Run the CLI with arguments and capture its text output."""
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *(str(argument) for argument in arguments)],
        capture_output=True,
        cwd=PROJECT_ROOT,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("filename", "data_uri_prefix"),
    [
        ("test.png", "data:image/png;base64,"),
        ("test.jpg", "data:image/jpeg;base64,"),
        ("test.svg", "data:image/svg+xml;base64,"),
    ],
)
def test_cli_prints_data_uri_for_supported_images(
    filename: str, data_uri_prefix: str
) -> None:
    """A supported image fixture is printed as the matching Data URI."""
    result = run_cli(FIXTURES_DIR / filename)

    assert result.returncode == 0
    assert result.stdout.startswith(data_uri_prefix)
    assert result.stderr == ""


def test_cli_without_arguments_prints_usage_and_exits_one() -> None:
    """Omitting the media path reports usage as an error."""
    result = run_cli()

    assert result.returncode == 1
    assert "usage" in result.stderr.lower()


def test_cli_help_prints_usage_to_stderr() -> None:
    """The help option writes CLI usage information to standard error."""
    result = run_cli("--help")

    assert "usage" in result.stderr.lower()


def test_cli_reports_nonexistent_file_and_exits_one() -> None:
    """A missing input path is reported as an error."""
    result = run_cli(FIXTURES_DIR / "does-not-exist.png")

    assert result.returncode == 1
    assert "does-not-exist.png" in result.stderr


def test_cli_reports_unsupported_extension_and_exits_one(tmp_path: Path) -> None:
    """An unsupported input extension is reported as an error."""
    unsupported_file = tmp_path / "media.txt"
    unsupported_file.write_text("not media")

    result = run_cli(unsupported_file)

    assert result.returncode == 1
    assert "unsupported" in result.stderr.lower()
