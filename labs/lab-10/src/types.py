from enum import Enum
from pydantic import BaseModel, field_validator


class MediaType(str, Enum):
    """All MIME types supported by this library."""
    PNG = "image/png"
    JPEG = "image/jpeg"
    GIF = "image/gif"
    WEBP = "image/webp"
    SVG = "image/svg+xml"
    MP3 = "audio/mpeg"
    WAV = "audio/wav"
    OGG = "audio/ogg"
    MP4 = "video/mp4"
    WEBM = "video/webm"


class MediaCategory(str, Enum):
    """The three supported media categories."""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class DataURI(BaseModel):
    """A parsed Data URI with its components separated."""
    media_type: MediaType
    category: MediaCategory
    base64: str
    raw: str

    @field_validator("base64")
    @classmethod
    def base64_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("base64 must not be empty")
        return v

    @field_validator("raw")
    @classmethod
    def raw_starts_with_data(cls, v: str) -> str:
        if not v.startswith("data:"):
            raise ValueError("raw must start with 'data:'")
        return v


EXTENSION_TO_MIME: dict[str, MediaType] = {
    "png": MediaType.PNG,
    "jpg": MediaType.JPEG,
    "jpeg": MediaType.JPEG,
    "gif": MediaType.GIF,
    "webp": MediaType.WEBP,
    "svg": MediaType.SVG,
    "mp3": MediaType.MP3,
    "wav": MediaType.WAV,
    "ogg": MediaType.OGG,
    "mp4": MediaType.MP4,
    "webm": MediaType.WEBM,
}


def get_category(mime_type: MediaType) -> MediaCategory:
    """
    Extract the category from a MIME type.
    e.g. "image/png" -> MediaCategory.IMAGE
    """
    prefix = mime_type.value.split("/")[0]
    return MediaCategory(prefix)