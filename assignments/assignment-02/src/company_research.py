import json
import sys

from src.llm import get_client, DEFAULT_MODEL
from src.schemas import CompanyResearch
from src.tools import web_search


SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for company information, news, culture, and job context.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The web search query"
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


def research_company(company_name: str, job_title: str, verbose: bool = False) -> CompanyResearch:
    client = get_client()

    messages = [
        {
            "role": "system",
            "content": (
                "You are researching a company for a job applicant. "
                "Use web_search to investigate company size, industry, "
                "recent developments, culture signals, and useful applicant context. "
                "Use 2-3 focused searches. Do not invent facts."
            ),
        },
        {
            "role": "user",
            "content": f"Research {company_name} for the role: {job_title}.",
        },
    ]

    # Hard guardrail to control cost and loops
    for step in range(3):
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=[SEARCH_TOOL],
            tool_choice="auto",
            parallel_tool_calls=False,
        )

        message = response.choices[0].message

        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls[:1]:
            args = json.loads(tool_call.function.arguments)

            results = web_search(
                args["query"],
                max_results=5,
                verbose=verbose,
            )

            simplified = [
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content"),
                }
                for r in results
            ]

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(simplified),
                }
            )

    if verbose:
        print("[DEBUG] Creating structured company research", file=sys.stderr)

    final_response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages + [
            {
                "role": "user",
                "content": (
                    "Using only the research above, produce the final structured "
                    "company research. Include URLs used in sources. "
                    "Use null or empty lists when information was not verified."
                ),
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "company_research",
                "strict": True,
                "schema": CompanyResearch.model_json_schema(),
            },
        },
        max_tokens=4000,
    )

    research = CompanyResearch.model_validate_json(
        final_response.choices[0].message.content
    )

    if verbose:
        print("[DEBUG] Company research validation: passed", file=sys.stderr)

    return research
