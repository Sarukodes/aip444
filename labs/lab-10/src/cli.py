"""Command-line interface for encoding media files as Data URIs."""

import sys
from os.path import dirname


SCRIPT_DIRECTORY = dirname(__file__)
PROJECT_ROOT = dirname(SCRIPT_DIRECTORY)

if SCRIPT_DIRECTORY in sys.path:
    sys.path.remove(SCRIPT_DIRECTORY)
sys.path.insert(0, PROJECT_ROOT)

import asyncio

from src import encode_file


USAGE = "Usage: python src/cli.py <media-file>\n"


def main() -> int:
    """Encode the file supplied on the command line and print its Data URI."""
    arguments = sys.argv[1:]

    if arguments == ["--help"] or arguments == ["-h"]:
        sys.stderr.write(USAGE)
        return 0

    if len(arguments) != 1:
        sys.stderr.write(USAGE)
        return 1

    file_path = arguments[0]
    try:
        data_uri = asyncio.run(encode_file(file_path))
    except FileNotFoundError:
        sys.stderr.write(f"Error: file not found: {file_path}\n")
        return 1
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    sys.stdout.write(data_uri.raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
