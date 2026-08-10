import json
import sys
from pathlib import Path

from src.llm import (
    DEFAULT_MODEL,
    get_client,
    set_llm_verbose,
)
from src.schemas import GapAnalysis
from src.tools import web_search


RESUME_PATH = Path("data/resume/resume.json")
MARKET_PATH = Path("data/analysis/market-analysis.json")

GAP_JSON_PATH = Path(
    "data/analysis/gap-analysis.json"
)

GAP_REPORT_PATH = Path(
    "reports/gap-analysis.md"
)


SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for one specific current resource "
            "that can help address an important resume gap."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string"
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


def generate_gap_analysis(
    verbose: bool = False,
) -> GapAnalysis:

    set_llm_verbose(verbose)

    if not RESUME_PATH.exists():
        raise RuntimeError(
            "Missing data/resume/resume.json"
        )

    if not MARKET_PATH.exists():
        raise RuntimeError(
            "Missing data/analysis/market-analysis.json"
        )

    resume = json.loads(
        RESUME_PATH.read_text(
            encoding="utf-8"
        )
    )

    market = json.loads(
        MARKET_PATH.read_text(
            encoding="utf-8"
        )
    )

    client = get_client()

    # --------------------------------------------------
    # STEP 1: Let the LLM choose ONE useful web search
    # --------------------------------------------------

    research_prompt = {
        "resume_hard_skills":
            resume.get("hard_skills", []),

        "resume_certifications":
            resume.get(
                "certifications_training",
                [],
            ),

        "market_required_skills":
            market.get(
                "common_required_skills",
                [],
            ),

        "market_trends":
            market.get(
                "notable_trends",
                [],
            ),
    }

    if verbose:
        print(
            "[DEBUG] Asking LLM to choose one gap-research query",
            file=sys.stderr,
        )

    research_response = (
        client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Review the candidate skills and market data. "
                        "Choose the single most useful current resource "
                        "to research for an important candidate gap. "
                        "Make exactly ONE web_search tool call. "
                        "Do not search for every skill."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        research_prompt,
                        indent=2,
                    ),
                },
            ],
            tools=[SEARCH_TOOL],
            tool_choice={
                "type": "function",
                "function": {
                    "name": "web_search"
                },
            },
            parallel_tool_calls=False,
            max_tokens=500,
            temperature=0,
        )
    )

    message = (
        research_response
        .choices[0]
        .message
    )

    research_results = []
    research_query = None

    if message.tool_calls:

        # Hard cost guardrail:
        # use ONLY the first tool call.
        tool_call = message.tool_calls[0]

        try:
            args = json.loads(
                tool_call.function.arguments
            )

            research_query = args.get(
                "query"
            )

        except json.JSONDecodeError:
            research_query = None

        if not research_query:
            research_query = (
                "official cloud DevOps training "
                "for software developers"
            )

        research_results = web_search(
            research_query,
            max_results=5,
            verbose=verbose,
        )

    if verbose:
        print(
            "[DEBUG] Gap research limited to 1 web search",
            file=sys.stderr,
        )

    simplified_research = [
        {
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content"),
        }
        for item in research_results
    ]

    # --------------------------------------------------
    # STEP 2: Structured gap analysis
    # --------------------------------------------------

    final_context = {
        "resume": resume,
        "market_analysis": market,
        "web_research": {
            "query": research_query,
            "results": simplified_research,
        },
    }

    if verbose:
        print(
            "[DEBUG] Creating structured gap analysis",
            file=sys.stderr,
        )

    final_response = (
        client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a practical career gap-analysis "
                        "assistant. Compare the candidate resume "
                        "against the supplied job-market analysis. "

                        "Identify strengths, missing or "
                        "underrepresented qualifications, and "
                        "unique value. "

                        "Create between 3 and 6 meaningful gaps only. "

                        "Every gap must be classified as exactly one "
                        "of: Quick win, Short-term, Medium-term, "
                        "or Long-term. "

                        "Recommendations must be concrete and "
                        "actionable. Keep each reason and action "
                        "concise. "

                        "Never invent candidate skills, experience, "
                        "certifications, or dates. "

                        "Do not describe completed certifications "
                        "as upcoming. "

                        "Use URLs from the supplied web research "
                        "only when that research actually supports "
                        "a recommendation."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        final_context,
                        indent=2,
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "gap_analysis",
                    "strict": True,
                    "schema":
                        GapAnalysis.model_json_schema(),
                },
            },
            max_tokens=5000,
            temperature=0,
        )
    )

    raw = (
        final_response
        .choices[0]
        .message
        .content
    )

    analysis = (
        GapAnalysis.model_validate_json(
            raw
        )
    )

    GAP_JSON_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    GAP_JSON_PATH.write_text(
        analysis.model_dump_json(
            indent=2
        ),
        encoding="utf-8",
    )

    if verbose:
        print(
            "[DEBUG] Gap analysis validation: passed",
            file=sys.stderr,
        )

    # --------------------------------------------------
    # STEP 3: Markdown report
    # --------------------------------------------------

    report_response = (
        client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a concise Markdown resume gap-analysis "
                        "report. Include Strengths, Unique Value, "
                        "Gap Triage, and Overall Observations. "
                        "Clearly show each gap level and preserve "
                        "useful research URLs. Do not invent "
                        "candidate qualifications."
                    ),
                },
                {
                    "role": "user",
                    "content":
                        analysis.model_dump_json(
                            indent=2
                        ),
                },
            ],
            max_tokens=3500,
            temperature=0,
        )
    )

    GAP_REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    GAP_REPORT_PATH.write_text(
        report_response
        .choices[0]
        .message
        .content,
        encoding="utf-8",
    )

    if verbose:
        print(
            f"[DEBUG] Saved: {GAP_JSON_PATH}",
            file=sys.stderr,
        )

        print(
            f"[DEBUG] Saved: {GAP_REPORT_PATH}",
            file=sys.stderr,
        )

    return analysis


if __name__ == "__main__":
    generate_gap_analysis(
        verbose=True
    )