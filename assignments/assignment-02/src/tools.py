import sys

from tavily import TavilyClient

from src.config import TAVILY_API_KEY, validate_tavily_key


def web_search(query: str, max_results: int = 5, verbose: bool = False) -> list[dict]:
    if verbose:
        print(f'[DEBUG] Tool call: web_search("{query}")', file=sys.stderr)

    try:
        # Treat configuration and provider failures as unavailable evidence,
        # so the caller can still produce an inconclusive assessment.
        validate_tavily_key()

        client = TavilyClient(api_key=TAVILY_API_KEY)

        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
        )

        results = response.get("results", [])

        if verbose:
            print(
                f"[DEBUG] Search returned {len(results)} results",
                file=sys.stderr,
            )

        return results

    except Exception as exc:
        if verbose:
            print(f"[DEBUG] Web search failed: {exc}", file=sys.stderr)

        return []
