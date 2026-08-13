"""Tests for encoding media files as Base64 Data URIs."""

import asyncio
import base64
from pathlib import Path

import pytest

from src.encode import encode_file
from src.types import DataURI, MediaCategory, MediaType


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("filename", "media_type", "category"),
    [
        ("test.png", MediaType.PNG, MediaCategory.IMAGE),
        ("test.jpg", MediaType.JPEG, MediaCategory.IMAGE),
        ("test.svg", MediaType.SVG, MediaCategory.IMAGE),
        ("test.mp3", MediaType.MP3, MediaCategory.AUDIO),
    ],
)
def test_encode_file_returns_expected_data_uri(
    filename: str, media_type: MediaType, category: MediaCategory
) -> None:
    """Encoding supported fixtures preserves content and assigns its MIME type."""
    fixture_path = FIXTURES_DIR / filename

    result = asyncio.run(encode_file(fixture_path))

    assert isinstance(result, DataURI)
    assert result.media_type is media_type
    assert result.category is category
    assert result.raw.startswith(f"data:{media_type.value};base64,")
    assert base64.b64decode(result.base64) == fixture_path.read_bytes()


def test_encode_file_raises_for_nonexistent_file() -> None:
    """Encoding a missing path reports a filesystem error."""
    missing_path = FIXTURES_DIR / "does-not-exist.png"

    with pytest.raises(FileNotFoundError):
        asyncio.run(encode_file(missing_path))


def test_encode_file_raises_for_unsupported_extension(tmp_path: Path) -> None:
    """Encoding a non-media extension is rejected."""
    unsupported_path = tmp_path / "media.txt"
    unsupported_path.write_bytes(b"not media")

    with pytest.raises(ValueError):
        asyncio.run(encode_file(unsupported_path))


def test_encode_file_raises_for_empty_file(tmp_path: Path) -> None:
    """Encoding an empty supported media file is rejected."""
    empty_path = tmp_path / "empty.png"
    empty_path.write_bytes(b"")

    with pytest.raises(ValueError):
        asyncio.run(encode_file(empty_path))


def test_encode_file_supports_paths_containing_spaces(tmp_path: Path) -> None:
    """Encoding a supported file works when its path contains spaces."""
    fixture_path = tmp_path / "media files" / "sample image.png"
    fixture_path.parent.mkdir()
    fixture_path.write_bytes(b"image bytes")

    result = asyncio.run(encode_file(fixture_path))

    assert result.media_type is MediaType.PNG
    assert base64.b64decode(result.base64) == b"image bytes"
