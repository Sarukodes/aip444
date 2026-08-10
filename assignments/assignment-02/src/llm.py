import sys

from openai import OpenAI

from src.config import OPENROUTER_API_KEY, validate_openrouter_key


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-2.5-flash-lite"

_VERBOSE = False


def set_llm_verbose(verbose: bool) -> None:
    global _VERBOSE
    _VERBOSE = verbose


class _CompletionsProxy:
    def __init__(self, real_completions):
        self._real = real_completions

    def create(self, *args, **kwargs):
        model = kwargs.get("model", DEFAULT_MODEL)

        if _VERBOSE:
            print(
                f"[DEBUG] LLM call: {model}",
                file=sys.stderr,
            )

        response = self._real.create(*args, **kwargs)

        if _VERBOSE and getattr(response, "usage", None):
            usage = response.usage

            prompt_tokens = getattr(
                usage,
                "prompt_tokens",
                None,
            )

            completion_tokens = getattr(
                usage,
                "completion_tokens",
                None,
            )

            total_tokens = getattr(
                usage,
                "total_tokens",
                None,
            )

            print(
                "[DEBUG] LLM usage: "
                f"prompt={prompt_tokens}, "
                f"completion={completion_tokens}, "
                f"total={total_tokens}",
                file=sys.stderr,
            )

        return response


class _ChatProxy:
    def __init__(self, real_chat):
        self.completions = _CompletionsProxy(
            real_chat.completions
        )


class OpenRouterClientProxy:
    def __init__(self, real_client):
        self.chat = _ChatProxy(real_client.chat)


def get_client():
    validate_openrouter_key()

    real_client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
    )

    return OpenRouterClientProxy(real_client)