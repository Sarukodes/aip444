from pathlib import Path
from .types import DataURI


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
    # TODO: implement
    raise NotImplementedError


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
    # TODO: implement
    raise NotImplementedError


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
    # TODO: implement
    raise NotImplementedError