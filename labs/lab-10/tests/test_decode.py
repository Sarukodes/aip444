"""Tests for parsing and decoding Base64 Data URIs."""

import asyncio
from pathlib import Path

import pytest

from src.decode import decode_to_bytes, parse_data_uri
from src.encode import encode_file
from src.types import MediaCategory, MediaType


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_data_uri_extracts_mime_type() -> None:
    """Parsing a Data URI identifies its MIME type and media category."""
    uri = "data:image/png;base64,aGVsbG8="

    result = parse_data_uri(uri)

    assert result.media_type is MediaType.PNG
    assert result.category is MediaCategory.IMAGE


def test_parse_data_uri_extracts_base64_payload() -> None:
    """Parsing a Data URI preserves the Base64 payload and original URI."""
    uri = "data:image/png;base64,aGVsbG8="

    result = parse_data_uri(uri)

    assert result.base64 == "aGVsbG8="
    assert result.raw == uri


def test_decode_to_bytes_decodes_base64_payload() -> None:
    """Decoding a valid Data URI returns its original bytes."""
    uri = "data:image/png;base64,aGVsbG8="

    assert decode_to_bytes(uri) == b"hello"


def test_encode_then_decode_round_trip_preserves_fixture_bytes() -> None:
    """A PNG fixture survives encode and decode without byte changes."""
    fixture_path = FIXTURES_DIR / "test.png"

    uri = asyncio.run(encode_file(fixture_path))

    assert decode_to_bytes(uri.raw) == fixture_path.read_bytes()


@pytest.mark.parametrize(
    "uri",
    [
        "image/png;base64,aGVsbG8=",
        "data:image/png,aGVsbG8=",
        "data:image/bmp;base64,aGVsbG8=",
        "data:image/png;base64,not-valid-base64!",
    ],
)
def test_parse_data_uri_rejects_invalid_uri(uri: str) -> None:
    """Parsing rejects malformed, unsupported, and invalidly encoded URIs."""
    with pytest.raises(ValueError):
        parse_data_uri(uri)
