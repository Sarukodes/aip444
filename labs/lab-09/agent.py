import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from agents import (
    Agent,
    Model,
    ModelProvider,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    RunHooks,
    Runner,
    Tool,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI

from tools import (
    assess_credibility,
    read_url,
    save_report,
    web_search,
)


load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "minimax/minimax-m2.7"
MAX_TURNS = 25

SYSTEM_PROMPT_PATH = Path(__file__).with_name("SYSTEM_PROMPT.md")


class CustomModelProvider(ModelProvider):
    """Provide an OpenRouter model to the OpenAI Agents SDK."""

    def __init__(
        self,
        client: AsyncOpenAI,
        default_model: str,
    ) -> None:
        self.client = client
        self.default_model = default_model

    def get_model(self, model_name: str | None) -> Model:
        selected_model = model_name or self.default_model

        return OpenAIChatCompletionsModel(
            model=selected_model,
            openai_client=self.client,
        )


class TraceHooks(RunHooks):
    """Print important events from the agent loop."""

    def __init__(self) -> None:
        self.event_number = 0

    def print_event(self, message: str) -> None:
        self.event_number += 1
        print(f"\n[TRACE {self.event_number}] {message}")

    async def on_agent_start(
        self,
        context,
        agent,
    ) -> None:
        self.print_event(
            f"Agent started: {agent.name}"
        )

    async def on_llm_start(
        self,
        context,
        agent,
        system_prompt,
        input_items,
    ) -> None:
        self.print_event(
            f"Sending request to model for agent: {agent.name}"
        )

    async def on_llm_end(
        self,
        context,
        agent,
        response,
    ) -> None:
        output_count = len(response.output)

        self.print_event(
            f"Model response received with "
            f"{output_count} output item(s)"
        )

    async def on_tool_start(
        self,
        context,
        agent,
        tool: Tool,
    ) -> None:
        self.print_event(
            f"Tool started: {tool.name}"
        )

    async def on_tool_end(
        self,
        context,
        agent,
        tool: Tool,
        result: object,
    ) -> None:
        result_text = str(result)

        if len(result_text) > 1500:
            result_text = (
                result_text[:1500]
                + "\n[Tool result preview truncated.]"
            )

        self.print_event(
            f"Tool completed: {tool.name}\n"
            f"Result preview:\n{result_text}"
        )

    async def on_agent_end(
        self,
        context,
        agent,
        output: Any,
    ) -> None:
        self.print_event(
            f"Agent completed: {agent.name}"
        )


def load_system_prompt() -> str:
    """Load instructions from SYSTEM_PROMPT.md."""

    if not SYSTEM_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"System prompt not found: {SYSTEM_PROMPT_PATH}"
        )

    prompt = SYSTEM_PROMPT_PATH.read_text(
        encoding="utf-8"
    ).strip()

    if not prompt:
        raise ValueError(
            "SYSTEM_PROMPT.md is empty."
        )

    return prompt


def get_source_url() -> str:
    """Get the source URL from the command line or user input."""

    if len(sys.argv) > 1:
        source_url = sys.argv[1].strip()
    else:
        source_url = input(
            "Enter the source URL to evaluate: "
        ).strip()

    if not source_url.startswith(
        ("http://", "https://")
    ):
        raise ValueError(
            "The source URL must begin with "
            "http:// or https://."
        )

    return source_url


async def main() -> None:
    """Configure and run the credibility analyzer agent."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    model_name = os.getenv(
        "MODEL_NAME",
        DEFAULT_MODEL,
    )

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY was not found "
            "in the .env file."
        )

    if not tavily_key:
        raise ValueError(
            "TAVILY_API_KEY was not found "
            "in the .env file."
        )

    source_url = get_source_url()
    system_prompt = load_system_prompt()

    openrouter_client = AsyncOpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
    )

    model_provider = CustomModelProvider(
        client=openrouter_client,
        default_model=model_name,
    )

    # OpenAI-hosted tracing requires an OpenAI platform key.
    # This project prints a local trace instead.
    set_tracing_disabled(disabled=True)

    credibility_agent = Agent(
        name="Source Credibility Analyzer",
        instructions=system_prompt,

        # Naming the actual model prevents the SDK from applying
        # settings intended for its default OpenAI model.
        model=model_name,

        # OpenRouter requires reasoning for this model.
        model_settings=ModelSettings(
            extra_body={
                "reasoning": {
                    "effort": "low"
                }
            },
            parallel_tool_calls=False,
        ),

        tools=[
            read_url,
            web_search,
            assess_credibility,
            save_report,
        ],
    )

    print("=" * 70)
    print("SOURCE CREDIBILITY ANALYZER AGENT")
    print("=" * 70)
    print(f"Source: {source_url}")
    print(f"Model: {model_name}")
    print(f"Maximum turns: {MAX_TURNS}")

    result = await Runner.run(
        credibility_agent,
        input=(
            "Evaluate the credibility of this source thoroughly. "
            "Follow every investigation step, call "
            "assess_credibility before save_report, and save the "
            f"final Markdown report.\n\nSource URL: {source_url}"
        ),
        max_turns=MAX_TURNS,
        hooks=TraceHooks(),
        run_config=RunConfig(
            model_provider=model_provider,
        ),
    )

    print("\n" + "=" * 70)
    print("FINAL AGENT OUTPUT")
    print("=" * 70)
    print(result.final_output)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nAgent run cancelled.")

    except Exception as error:
        print(f"\nError: {error}")
        sys.exit(1)