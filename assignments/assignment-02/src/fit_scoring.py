import json
import sys

from src.llm import (
    DEFAULT_MODEL,
    get_client,
)
from src.schemas import (
    FitAssessment,
    FitMatchAnalysis,
    JobPosting,
)


STATUS_VALUE = {
    "met": 1.0,
    "partial": 0.5,
    "missing": 0.0,
}


BASE_WEIGHTS = {
    "required_skill": 60,
    "preferred_skill": 15,
    "experience": 15,
    "education": 10,
}


def _category_score(
    matches,
    category: str,
) -> int:

    relevant = [
        match
        for match in matches
        if match.category == category
    ]

    if not relevant:
        return 0

    total = sum(
        STATUS_VALUE[
            match.status
        ]
        for match in relevant
    )

    return round(
        100 * total / len(relevant)
    )


def assess_fit(
    job: JobPosting,
    resume: dict,
    verbose: bool = False,
) -> FitAssessment:

    client = get_client()

    prompt = {
        "job": job.model_dump(),
        "resume": resume,
    }

    response = (
        client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Compare this candidate against the job. "
                        "Create one match item for every required "
                        "skill, every preferred skill, and the job's "
                        "experience and education requirement when "
                        "those fields exist. "
                        "Status must be met, partial, or missing. "
                        "Only mark met when the resume provides "
                        "direct evidence. Projects can demonstrate "
                        "technical skills but must not be treated as "
                        "years of professional experience."
                    ),
                },
                {
                    "role": "user",
                    "content":
                    json.dumps(
                        prompt,
                        indent=2,
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name":
                    "fit_match_analysis",
                    "strict": True,
                    "schema":
                    FitMatchAnalysis
                    .model_json_schema(),
                },
            },
            max_tokens=4500,
            temperature=0,
        )
    )

    match_analysis = (
        FitMatchAnalysis
        .model_validate_json(
            response
            .choices[0]
            .message
            .content
        )
    )

    matches = (
        match_analysis.matches
    )

    component_scores = {
        category:
        _category_score(
            matches,
            category,
        )
        for category
        in BASE_WEIGHTS
    }

    active_categories = []

    if job.required_skills:
        active_categories.append(
            "required_skill"
        )

    if job.preferred_skills:
        active_categories.append(
            "preferred_skill"
        )

    if job.experience_level:
        active_categories.append(
            "experience"
        )

    if job.education_requirements:
        active_categories.append(
            "education"
        )

    if not active_categories:
        active_categories = [
            "required_skill"
        ]

    active_weight = sum(
        BASE_WEIGHTS[c]
        for c in active_categories
    )

    weighted_total = sum(
        component_scores[c]
        * BASE_WEIGHTS[c]
        for c in active_categories
    )

    score = round(
        weighted_total
        / active_weight
    )

    if score >= 80:
        label = "Strong fit"
        recommendation = (
            "You should definitely apply. "
            "You match most of the important requirements."
        )

    elif score >= 50:
        label = "Good fit"
        recommendation = (
            "Apply. You meet a meaningful portion of the "
            "requirements and should emphasize your strongest "
            "matching experience."
        )

    elif score >= 30:
        label = "Stretch"
        recommendation = (
            "This is a stretch, but it can still be worth applying "
            "if the role interests you. Position your transferable "
            "skills clearly and address the largest gaps honestly."
        )

    else:
        label = "Growth target"
        recommendation = (
            "The role currently has significant gaps, but the "
            "posting is useful as a roadmap for what to build next."
        )

    if verbose:
        for category in active_categories:
            print(
                "[DEBUG] Fit scoring: "
                f"{category}="
                f"{component_scores[category]}% "
                f"(weight {BASE_WEIGHTS[category]})",
                file=sys.stderr,
            )

        print(
            "[DEBUG] Overall fit: "
            f"{score}% — {label}",
            file=sys.stderr,
        )

    return FitAssessment(
        score=score,
        label=label,
        recommendation=recommendation,
        component_scores=
        component_scores,
        component_weights=
        BASE_WEIGHTS,
        matches=matches,
    )