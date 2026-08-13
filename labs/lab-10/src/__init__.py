"""Public API for encoding and decoding media Data URIs."""

from .encode import encode_bytes, encode_file
from .decode import decode_to_bytes, decode_to_file, parse_data_uri
from .types import (
    EXTENSION_TO_MIME,
    DataURI,
    MediaCategory,
    MediaType,
    get_category,
)

__all__ = [
    "DataURI",
    "EXTENSION_TO_MIME",
    "MediaCategory",
    "MediaType",
    "decode_to_bytes",
    "decode_to_file",
    "encode_bytes",
    "encode_file",
    "get_category",
    "parse_data_uri",
]
