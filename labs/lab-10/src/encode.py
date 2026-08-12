from pathlib import Path
from .types import DataURI


async def encode_file(file_path: str | Path) -> DataURI:
    """
    Read a media file from disk and return it as a
    Data URI.

    Args:
        file_path: Path to the media file

    Returns:
        A DataURI object with the encoded content

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file extension is unsupported
        ValueError: If the file is empty (0 bytes)
    """
    # TODO: implement
    raise NotImplementedError


def encode_bytes(
    data: bytes, mime_type: str
) -> DataURI:
    """
    Encode raw bytes as a Data URI with the given
    MIME type.

    Args:
        data: The raw binary data
        mime_type: A valid MIME type string

    Returns:
        A DataURI object

    Raises:
        ValueError: If the MIME type is unsupported
        ValueError: If the data is empty
    """
    # TODO: implement
    raise NotImplementedError