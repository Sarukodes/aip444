import os
import sys
from typing import Any

from pydantic import BaseModel, Field
from tavily import TavilyClient


class LookupErrorArguments(BaseModel):
    """Arguments accepted by the lookup_error tool."""

    query: str = Field(
        ...,
        min_length=3,
        description="A concise web-search query based on the error in the screenshot.",
    )


LOOKUP_ERROR_TOOL = {
    "type": "function",
    "function": {
        "name": "lookup_error",
        "description": (
            "Searches the web for current technical documentation, coding "
            "errors, framework changes, and possible debugging solutions."
        ),
        "parameters": LookupErrorArguments.model_json_schema(),
    },
}


def lookup_error(query: str) -> dict[str, Any]:
    """Search Tavily and return simplified, source-based results."""

    arguments = LookupErrorArguments(query=query)

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY was not found. Add it to the project .env file."
        )

    print(
        f"[debug] Searching Tavily for: {arguments.query}",
        file=sys.stderr,
    )

    client = TavilyClient(api_key=api_key)

    response = client.search(
        query=arguments.query,
        search_depth="advanced",
        max_results=5,
        include_answer=True,
    )

    simplified_results = []

    for result in response.get("results", []):
        simplified_results.append(
            {
                "title": result.get("title", "Untitled"),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
            }
        )

    return {
        "query": arguments.query,
        "answer": response.get("answer", ""),
        "results": simplified_results,
    }