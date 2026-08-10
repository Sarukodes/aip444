import json
import sys
from pathlib import Path

from src.llm import get_client, DEFAULT_MODEL
from src.pdf_utils import extract_pdf_text
from src.schemas import ResumeData


def extract_resume(resume_path: str, verbose: bool = False) -> ResumeData:
    path = Path(resume_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {resume_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("For now, provide the resume as a PDF.")

    if verbose:
        print(f"[DEBUG] Extracting resume: {path.name}", file=sys.stderr)

    text = extract_pdf_text(str(path))

    client = get_client()

    prompt = f"""
Extract the resume below into the required structured schema.

Rules:
- Only use information explicitly supported by the resume.
- Do not invent skills, experience, achievements, certifications, or education.
- Use [] when a category has no supported information.
- Keep technologies as individual hard skills where possible.
- Work experience should preserve the role, company, duration,
  responsibilities, and achievements found in the resume.
- Projects and accomplishments should include concrete project work.
- Keywords/domain expertise should include relevant concepts such as
  APIs, AI agents, RAG, Git, Agile, CI/CD, etc. only when supported.
- Do not infer years of experience that are not explicitly stated.

RESUME:
{text}
"""

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise resume extraction system. "
                    "Never invent candidate qualifications."
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
                "name": "resume_data",
                "strict": True,
                "schema": ResumeData.model_json_schema(),
            },
        },
        max_tokens=5000,
    )

    resume = ResumeData.model_validate_json(
        response.choices[0].message.content
    )

    if verbose:
        print(
            f"[DEBUG] Extracted {len(resume.hard_skills)} hard skills",
            file=sys.stderr,
        )
        print(
            f"[DEBUG] Extracted {len(resume.work_experience)} work experiences",
            file=sys.stderr,
        )
        print(
            "[DEBUG] Resume structured output validation: passed",
            file=sys.stderr,
        )

    return resume


def save_resume(resume: ResumeData) -> None:
    output = Path("data/resume/resume.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(resume.model_dump(), indent=2),
        encoding="utf-8",
    )