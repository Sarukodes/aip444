import json
import sys
from datetime import date, datetime
from pathlib import Path

from src.llm import get_client, DEFAULT_MODEL
from src.pdf_utils import extract_pdf_text
from src.schemas import JobPosting


def extract_job(pdf_path: str, verbose: bool = False) -> JobPosting:
    path = Path(pdf_path)

    text = extract_pdf_text(pdf_path)

    # Approximate the PDF capture date using the file modification time.
    capture_date = datetime.fromtimestamp(
        path.stat().st_mtime
    ).date()

    today = date.today()

    if verbose:
        print(
            f"[DEBUG] Extracting posting: {path.name}",
            file=sys.stderr,
        )
        print(
            f"[DEBUG] Capture date: {capture_date}",
            file=sys.stderr,
        )
        print(
            f"[DEBUG] Today's date: {today}",
            file=sys.stderr,
        )

    client = get_client()

    prompt = f"""
Extract the job posting below into the required structured schema.

Today's date: {today.isoformat()}
PDF capture date: {capture_date.isoformat()}

Follow these rules carefully:

GENERAL EXTRACTION RULES
- Only extract information that is actually supported by the job posting.
- Never guess or invent missing information.
- Use null when a scalar field is not listed.
- Use [] when a list field has no supported values.
- Do not add information from general knowledge.
- Do not add company research during this step.
- company_research must be null because it will be populated later
  using the web search tool.

REQUIRED VS PREFERRED SKILLS
- required_skills should contain only hard skills, technologies,
  platforms, tools, or technical abilities that the posting clearly
  presents as required or expected for the candidate.
- A skill should be treated as required when it appears under wording
  such as:
  "required", "requirements", "must have", "you have",
  "qualifications", "minimum qualifications", or equivalent wording.
- preferred_skills should contain only skills that are explicitly
  optional or preferred.
- Treat wording such as:
  "preferred", "nice to have", "asset", "bonus",
  "would be an advantage", or "preferred qualifications"
  as preferred_skills.
- Do not classify general responsibilities as skills.
- Do not extract every noun or technology mentioned in the posting
  as a skill.
- Do not add technologies mentioned only as examples unless the
  posting expects the candidate to know or use them.
- Do not duplicate the same skill in both required_skills and
  preferred_skills.
- If a skill appears as both required and preferred, keep it only in
  required_skills.
- Keep skill names concise and consistent.

EXPERIENCE AND EDUCATION
- experience_level must only contain experience or seniority that is
  supported by the posting.
- Do not convert project work into professional experience.
- education_requirements must only contain education explicitly
  required or accepted by the posting.

SALARY
- Preserve the salary wording and currency as closely as possible.
- Do not infer a currency if one is not shown.
- Do not convert hourly pay into annual salary.
- Do not calculate or modify compensation values.

POSTING DATE
- posting_date_text should preserve the wording shown in the posting,
  such as "Posted 3 days ago" or an exact date.
- Calculate posting_age_days from the posting date when possible.
- If the posting uses a relative date such as "Posted 3 days ago",
  calculate it relative to the PDF capture date.
- If no posting date can be determined, set posting_age_days to null.

RESPONSIBILITIES
- key_responsibilities should contain actual responsibilities from
  the posting.
- Keep responsibilities separate from required_skills and
  preferred_skills.
- Do not invent responsibilities.

JOB POSTING:
{text}
"""

    schema = JobPosting.model_json_schema()

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise job-posting extraction system. "
                    "Extract only information supported by the supplied "
                    "posting. Never invent information. Be conservative "
                    "when classifying skills as required versus preferred."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "job_posting",
                "strict": True,
                "schema": schema,
            },
        },
        temperature=0,
        max_tokens=6000,
    )

    raw = response.choices[0].message.content

    if not raw:
        raise RuntimeError(
            "The LLM returned an empty response during job extraction."
        )

    job = JobPosting.model_validate_json(raw)

    # Remove duplicates while preserving order.
    job.required_skills = list(
        dict.fromkeys(job.required_skills)
    )

    job.preferred_skills = list(
        dict.fromkeys(job.preferred_skills)
    )

    # If the exact same skill appears in both lists,
    # keep it only as required.
    required_lower = {
        skill.strip().lower()
        for skill in job.required_skills
    }

    job.preferred_skills = [
        skill
        for skill in job.preferred_skills
        if skill.strip().lower() not in required_lower
    ]

    if verbose:
        print(
            f"[DEBUG] Extracted "
            f"{len(job.required_skills)} required skills, "
            f"{len(job.preferred_skills)} preferred skills",
            file=sys.stderr,
        )

        if job.salary_range:
            print(
                f"[DEBUG] Salary field: {job.salary_range}",
                file=sys.stderr,
            )
        else:
            print(
                "[DEBUG] Salary field: not found in posting",
                file=sys.stderr,
            )

        print(
            f"[DEBUG] posting_age_days: "
            f"{job.posting_age_days}",
            file=sys.stderr,
        )

        print(
            "[DEBUG] Structured output validation: passed",
            file=sys.stderr,
        )

    return job


def save_job(job: JobPosting, output_path: str) -> None:
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            job.model_dump(),
            indent=2,
        ),
        encoding="utf-8",
    )