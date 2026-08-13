import base64
from pathlib import Path

from .types import (
    EXTENSION_TO_MIME,
    DataURI,
    MediaType,
    get_category,
)


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
    path = Path(file_path)
    extension = path.suffix.lstrip(".").lower()

    if extension not in EXTENSION_TO_MIME:
        raise ValueError(f"Unsupported file extension: {path.suffix}")

    return encode_bytes(path.read_bytes(), EXTENSION_TO_MIME[extension].value)


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
    if not data:
        raise ValueError("Data must not be empty")

    try:
        media_type = MediaType(mime_type)
    except ValueError as exc:
        raise ValueError(f"Unsupported MIME type: {mime_type}") from exc

    payload = base64.b64encode(data).decode("ascii")
    raw = f"data:{media_type.value};base64,{payload}"

    return DataURI(
        media_type=media_type,
        category=get_category(media_type),
        base64=payload,
        raw=raw,
    )
