import argparse
import base64
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, UnidentifiedImageError

from tools import LOOKUP_ERROR_TOOL, lookup_error


MAX_IMAGE_SIZE = 1024
JPEG_QUALITY = 85
MAX_TOOL_ROUNDS = 5

# The model can also be overridden using OPENROUTER_MODEL in .env.
DEFAULT_MODEL = "google/gemini-3-flash-preview"


def format_bytes(size: int) -> str:
    """Convert a byte count into a readable value."""

    if size < 1024:
        return f"{size} bytes"

    if size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"

    return f"{size / (1024 * 1024):.2f} MB"


def process_image(path: str) -> str:
    """
    Resize an image, convert it to JPEG, and return a Base64 string.
    """

    image_path = Path(path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if not image_path.is_file():
        raise ValueError(f"The supplied path is not a file: {image_path}")

    original_size = image_path.stat().st_size

    try:
        with Image.open(image_path) as image:
            original_dimensions = image.size

            # JPEG does not support transparency.
            image = image.convert("RGB")

            # Resize proportionally without enlarging small images.
            image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))

            processed_dimensions = image.size

            buffer = io.BytesIO()

            image.save(
                buffer,
                format="JPEG",
                quality=JPEG_QUALITY,
                optimize=True,
            )

    except UnidentifiedImageError as error:
        raise ValueError(
            f"Unsupported or invalid image file: {image_path}"
        ) from error
    except OSError as error:
        raise ValueError(
            f"Unable to process image: {image_path}"
        ) from error

    jpeg_bytes = buffer.getvalue()
    base64_string = base64.b64encode(jpeg_bytes).decode("utf-8")

    print(
        f"[debug] Original image: {format_bytes(original_size)} "
        f"({original_dimensions[0]}x{original_dimensions[1]})",
        file=sys.stderr,
    )

    print(
        f"[debug] Processed JPEG: {format_bytes(len(jpeg_bytes))} "
        f"({processed_dimensions[0]}x{processed_dimensions[1]})",
        file=sys.stderr,
    )

    print(
        f"[debug] Base64 string: {format_bytes(len(base64_string))} "
        f"({len(base64_string)} characters)",
        file=sys.stderr,
    )

    return base64_string


def load_system_prompt() -> str:
    """Load the debugging instructions from SYSTEM_PROMPT.md."""

    prompt_path = Path(__file__).with_name("SYSTEM_PROMPT.md")

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"System prompt not found: {prompt_path}"
        )

    prompt = prompt_path.read_text(encoding="utf-8").strip()

    if not prompt:
        raise ValueError("SYSTEM_PROMPT.md is empty.")

    return prompt


def load_environment() -> None:
    """Load the .env file from the repository root."""

    repository_root = Path(__file__).resolve().parents[2]
    env_path = repository_root / ".env"

    load_dotenv(env_path)

    if not os.getenv("OPENROUTER_API_KEY"):
        raise RuntimeError(
            f"OPENROUTER_API_KEY was not found in {env_path}"
        )

    if not os.getenv("TAVILY_API_KEY"):
        raise RuntimeError(
            f"TAVILY_API_KEY was not found in {env_path}"
        )


def create_client() -> OpenAI:
    """Create an OpenAI-compatible client for OpenRouter."""

    return OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )


def make_assistant_message(message: Any) -> dict[str, Any]:
    """
    Convert an SDK response message into a dictionary that can be
    included in the next request.
    """

    assistant_message: dict[str, Any] = {
        "role": "assistant",
        "content": message.content,
    }

    if message.tool_calls:
        assistant_message["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
            for tool_call in message.tool_calls
        ]

    return assistant_message


def execute_tool_call(tool_call: Any) -> dict[str, Any]:
    """Execute one tool call requested by the model."""

    tool_name = tool_call.function.name

    print(
        f"[debug] Model requested tool: {tool_name}",
        file=sys.stderr,
    )

    if tool_name != "lookup_error":
        return {
            "error": f"Unknown tool requested: {tool_name}"
        }

    try:
        arguments = json.loads(tool_call.function.arguments)

        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a JSON object.")

        return lookup_error(query=arguments["query"])

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return {
            "error": f"Invalid lookup_error arguments: {error}"
        }

    except Exception as error:
        return {
            "error": f"Web search failed: {error}"
        }


def analyze_image(image_path: str, user_prompt: str) -> str:
    """Send the image to the model and handle any tool calls."""

    load_environment()

    client = create_client()
    system_prompt = load_system_prompt()
    base64_image = process_image(image_path)

    model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)

    print(f"[debug] Model: {model}", file=sys.stderr)
    print("[debug] Sending image to OpenRouter...", file=sys.stderr)

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            "data:image/jpeg;base64,"
                            f"{base64_image}"
                        )
                    },
                },
            ],
        },
    ]

    for round_number in range(1, MAX_TOOL_ROUNDS + 1):
        print(
            f"[debug] Model request round: {round_number}",
            file=sys.stderr,
        )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[LOOKUP_ERROR_TOOL],
            tool_choice="auto",
        )

        assistant_response = response.choices[0].message
        messages.append(make_assistant_message(assistant_response))

        if not assistant_response.tool_calls:
            if not assistant_response.content:
                raise RuntimeError(
                    "The model returned an empty response."
                )

            return assistant_response.content

        for tool_call in assistant_response.tool_calls:
            tool_result = execute_tool_call(tool_call)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                    ),
                }
            )

    raise RuntimeError(
        f"The model exceeded the maximum of "
        f"{MAX_TOOL_ROUNDS} tool-calling rounds."
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        prog="img-debug",
        description=(
            "Analyze a screenshot using a vision-capable LLM "
            "and Tavily web search."
        ),
    )

    parser.add_argument(
        "image",
        help="Path to the terminal, IDE, or developer screenshot.",
    )

    parser.add_argument(
        "prompt",
        nargs="*",
        help="Optional instructions for analyzing the screenshot.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the img-debug command-line application."""

    arguments = parse_arguments()

    user_prompt = " ".join(arguments.prompt).strip()

    if not user_prompt:
        user_prompt = (
            "Analyze this screenshot, identify the error, "
            "research it when necessary, and give me a reliable fix."
        )

    try:
        result = analyze_image(
            image_path=arguments.image,
            user_prompt=user_prompt,
        )

        print()
        print(result)

    except KeyboardInterrupt:
        print("\nCancelled by user.", file=sys.stderr)
        raise SystemExit(130)

    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()