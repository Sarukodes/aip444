import os
from pathlib import Path

from dotenv import load_dotenv


ASSIGNMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

# Support either:
# aip444/.env
# or assignments/assignment-02/.env
ENV_CANDIDATES = [
    ASSIGNMENT_ROOT / ".env",
    REPO_ROOT / ".env",
]

LOADED_ENV = None

for env_path in ENV_CANDIDATES:
    if env_path.exists():
        load_dotenv(env_path)
        LOADED_ENV = env_path
        break


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def validate_openrouter_key() -> None:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY was not found. "
            f"Checked: {', '.join(str(p) for p in ENV_CANDIDATES)}"
        )


def validate_tavily_key() -> None:
    if not TAVILY_API_KEY:
        raise RuntimeError(
            "TAVILY_API_KEY was not found. "
            f"Checked: {', '.join(str(p) for p in ENV_CANDIDATES)}"
        )