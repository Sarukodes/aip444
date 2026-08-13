import base64
import binascii
from pathlib import Path

from .types import DataURI, MediaType, get_category


def _remove_base64_whitespace(payload: str) -> str:
    """Remove ASCII whitespace permitted in wrapped Base64 payloads."""
    return payload.translate(str.maketrans("", "", " \t\n\r\f\v"))


def parse_data_uri(uri: str) -> DataURI:
    """
    Parse a Data URI string into its components.

    Args:
        uri: A complete Data URI string
            (e.g. "data:image/png;base64,iVBOR...")

    Returns:
        A DataURI object with parsed components

    Raises:
        ValueError: If the string is not a valid Data URI
        ValueError: If the MIME type is unsupported
        ValueError: If the Base64 content is invalid
    """
    prefix = "data:"
    marker = ";base64,"

    if not uri.startswith(prefix) or marker not in uri:
        raise ValueError("URI must use the data:<mime>;base64,<payload> format")

    header, payload = uri[len(prefix):].split(marker, maxsplit=1)
    if not header:
        raise ValueError("Data URI MIME type must not be empty")

    try:
        media_type = MediaType(header)
    except ValueError as exc:
        raise ValueError(f"Unsupported MIME type: {header}") from exc

    normalized_payload = _remove_base64_whitespace(payload)

    try:
        base64.b64decode(normalized_payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Data URI payload is not valid Base64") from exc

    return DataURI(
        media_type=media_type,
        category=get_category(media_type),
        base64=normalized_payload,
        raw=uri,
    )


def decode_to_bytes(uri: str) -> bytes:
    """
    Decode a Data URI string back into raw binary data.

    Args:
        uri: A complete Data URI string

    Returns:
        The decoded binary data

    Raises:
        ValueError: If the URI is invalid
    """
    parsed_uri = parse_data_uri(uri)
    try:
        return base64.b64decode(parsed_uri.base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Data URI payload is not valid Base64") from exc


async def decode_to_file(
    uri: str, output_path: str | Path
) -> None:
    """
    Decode a Data URI and write the result to a file.

    Args:
        uri: A complete Data URI string
        output_path: Where to write the decoded file

    Raises:
        ValueError: If the URI is invalid
    """
    Path(output_path).write_bytes(decode_to_bytes(uri))
