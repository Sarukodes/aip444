import json

from src.llm import (
    DEFAULT_MODEL,
    get_client,
)
from src.schemas import (
    ApplicationAdvice,
    FitAssessment,
    JobPosting,
    LegitimacyAssessment,
)


def generate_application_advice(
    job: JobPosting,
    resume: dict,
    market_analysis: dict,
    gap_analysis: dict,
    fit: FitAssessment,
    legitimacy:
    LegitimacyAssessment,
):

    client = get_client()

    context = {
        "job": job.model_dump(),
        "resume": resume,
        "market_analysis":
        market_analysis,
        "gap_analysis":
        gap_analysis,
        "fit_assessment":
        fit.model_dump(),
        "legitimacy":
        legitimacy.model_dump(),
    }

    response = (
        client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a targeted job-application advisor. "
                        "Use only the supplied candidate evidence. "
                        "Do not invent professional experience or "
                        "achievements. Resume suggestions must be "
                        "specific edits or reframing suggestions, not "
                        "generic advice. Cover-letter guidance should "
                        "connect real candidate strengths to this "
                        "specific job/company. Interview questions "
                        "must be based on the posting requirements "
                        "and candidate gaps. Never encourage the user "
                        "to falsely claim a missing skill. Never "
                        "describe project, academic, or personal work "
                        "as equivalent to professional years of "
                        "experience. Never recommend adding a technology "
                        "to the resume unless the supplied resume shows "
                        "that the candidate used or studied it. For "
                        "missing skills, recommend learning or building "
                        "evidence instead of claiming proficiency. Always "
                        "acknowledge experience gaps honestly."
                        " Keep the response concise. Return at most "
                        "5 resume suggestions, 5 cover-letter points, "
                        "5 interview questions, 5 skills to brush up on, "
                        "4 company research topics, and 5 talking points."
                    ),
                },
                {
                    "role": "user",
                    "content":
                    json.dumps(
                        context,
                        indent=2,
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name":
                    "application_advice",
                    "strict": True,
                    "schema":
                    ApplicationAdvice
                    .model_json_schema(),
                },
            },
            max_tokens=8000,
            temperature=0,
        )
    )

    return (
        ApplicationAdvice
        .model_validate_json(
            response
            .choices[0]
            .message
            .content
        )
    )
