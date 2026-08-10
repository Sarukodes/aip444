import json
import sys

from src.llm import (
    DEFAULT_MODEL,
    get_client,
)
from src.schemas import (
    JobPosting,
    LegitimacyAssessment,
)
from src.tools import web_search
from src.whois_tool import whois_lookup


WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web to verify a company, its official "
            "website, careers page, recent information, employee "
            "presence, and a specific job posting."
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


WHOIS_TOOL = {
    "type": "function",
    "function": {
        "name": "whois_lookup",
        "description": (
            "Look up WHOIS registration information for an "
            "official-looking company domain. Do not use a job-board "
            "domain unless the job board itself is the employer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string"
                }
            },
            "required": ["domain"],
            "additionalProperties": False,
        },
    },
}


# A legitimacy verdict should be based on a focused external check, not an
# open-ended agent loop. This allows one Tavily search and one WHOIS lookup.
MAX_INVESTIGATION_ROUNDS = 2


def assess_legitimacy(
    job: JobPosting,
    posting_text: str,
    market_analysis: dict,
    verbose: bool = False,
) -> LegitimacyAssessment:

    client = get_client()

    messages = [
        {
            "role": "system",
            "content": (
                "You are a job-posting legitimacy investigator. "
                "Investigate whether the company and posting appear "
                "legitimate using web_search and whois_lookup. "

                "Check for an established company presence, official "
                "website and careers page, existence of the job, "
                "matching company domain, domain age, recent company "
                "information, suspicious salary, vague descriptions, "
                "upfront fees, requests for sensitive personal "
                "information, and suspicious contact methods. "

                "Privacy-protected WHOIS information alone is NOT "
                "a red flag. Never accuse a company of fraud without "
                "evidence. Clearly distinguish verified facts from "
                "unverified information. "

                "IMPORTANT COST RULE: You have only two investigation "
                "rounds: one focused web_search followed by one "
                "whois_lookup. Make at most one tool call per turn."
            ),
        },
        {
            "role": "user",
            "content": (
                "JOB:\n"
                + job.model_dump_json(indent=2)
                + "\n\nPOSTING TEXT:\n"
                + posting_text[:18000]
                + "\n\nMARKET CONTEXT:\n"
                + json.dumps(
                    market_analysis,
                    indent=2,
                )
            ),
        },
    ]

    tools = [
        WEB_SEARCH_TOOL,
        WHOIS_TOOL,
    ]

    # Hard cost guardrail: exactly two possible external calls in total.
    # The first establishes a web presence; the second checks the domain.
    for step in range(MAX_INVESTIGATION_ROUNDS):

        # First make sure web search is demonstrated.
        if step == 0:
            tool_choice = {
                "type": "function",
                "function": {
                    "name": "web_search"
                },
            }

        # Then make sure WHOIS is demonstrated.
        elif step == 1:
            tool_choice = {
                "type": "function",
                "function": {
                    "name": "whois_lookup"
                },
            }

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=False,
            max_tokens=1200,
            temperature=0,
        )

        message = response.choices[0].message

        messages.append(
            message.model_dump(
                exclude_none=True
            )
        )

        if not message.tool_calls:
            break

        # Execute only ONE real external tool call per round.
        # If the model requests more, return a controlled error
        # for the additional calls.
        for index, tool_call in enumerate(
            message.tool_calls
        ):

            if index >= 1:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            {
                                "error": (
                                    "Tool-call limit reached. "
                                    "Only one external tool call "
                                    "is executed per investigation "
                                    "round."
                                )
                            }
                        ),
                    }
                )
                continue

            try:
                args = json.loads(
                    tool_call.function.arguments
                )
            except json.JSONDecodeError:
                args = {}

            if not isinstance(args, dict):
                args = {}

            name = tool_call.function.name

            # --------------------------------------------
            # Tavily web search
            # --------------------------------------------

            if name == "web_search":

                query = args.get(
                    "query",
                    (
                        f"{job.company_name} "
                        f"{job.job_title} "
                        "official careers"
                    ),
                )

                results = web_search(
                    query,
                    max_results=5,
                    verbose=verbose,
                )

                simplified = [
                    {
                        "title": result.get(
                            "title"
                        ),
                        "url": result.get(
                            "url"
                        ),
                        "content": result.get(
                            "content"
                        ),
                    }
                    for result in results
                ]

                tool_result = simplified

            # --------------------------------------------
            # WHOIS
            # --------------------------------------------

            elif name == "whois_lookup":

                domain = args.get(
                    "domain",
                    "",
                )

                tool_result = whois_lookup(
                    domain,
                    verbose=verbose,
                )

            # --------------------------------------------
            # Unknown tool safety
            # --------------------------------------------

            else:
                tool_result = {
                    "error": (
                        f"Unknown tool: {name}"
                    )
                }

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        tool_result
                    ),
                }
            )

    # --------------------------------------------------
    # Final structured verdict
    # --------------------------------------------------

    if verbose:
        print(
            "[DEBUG] Creating structured legitimacy verdict",
            file=sys.stderr,
        )

    final_response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages
        + [
            {
                "role": "user",
                "content": (
                    "Using only the posting and investigation "
                    "evidence above, produce the final structured "
                    "legitimacy assessment. "

                    "Include green, yellow, and red signals when "
                    "supported by evidence. Include concise evidence "
                    "used to reach the verdict and source URLs where "
                    "available. "

                    "Do not treat missing information as proof of "
                    "fraud. Do not treat WHOIS privacy protection "
                    "alone as suspicious."
                ),
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": (
                    "legitimacy_assessment"
                ),
                "strict": True,
                "schema": (
                    LegitimacyAssessment
                    .model_json_schema()
                ),
            },
        },
        max_tokens=3500,
        temperature=0,
    )

    assessment = (
        LegitimacyAssessment
        .model_validate_json(
            final_response
            .choices[0]
            .message
            .content
        )
    )

    # --------------------------------------------------
    # Verbose observability
    # --------------------------------------------------

    if verbose:

        print(
            "[DEBUG] Legitimacy: "
            f"overall verdict — "
            f"{assessment.verdict} "
            f"({assessment.confidence_score}%)",
            file=sys.stderr,
        )

        for signal in assessment.signals:

            print(
                "[DEBUG] Legitimacy signal: "
                f"{signal.signal_type} - "
                f"{signal.signal}",
                file=sys.stderr,
            )

    return assessment
