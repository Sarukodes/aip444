import json
import sys
from pathlib import Path

from src.llm import get_client, DEFAULT_MODEL
from src.schemas import MarketAnalysis


JOBS_DIR = Path("data/jobs")
ANALYSIS_PATH = Path("data/analysis/market-analysis.json")
REPORT_PATH = Path("reports/market-analysis.md")


def generate_market_analysis(verbose: bool = False) -> MarketAnalysis:
    job_files = sorted(JOBS_DIR.glob("*.json"))

    if not job_files:
        raise RuntimeError("No extracted jobs found in data/jobs/")

    jobs = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in job_files
    ]

    if verbose:
        print(
            f"[DEBUG] Aggregating {len(jobs)} job postings",
            file=sys.stderr,
        )

    client = get_client()

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a job-market analyst. Analyze patterns across "
                    "the supplied structured job postings. Use concrete counts "
                    "and observations. Do not invent information."
                ),
            },
            {
                "role": "user",
                "content": (
                        f"You are analyzing exactly {len(jobs)} job postings.\n"
                        f"The total_postings field MUST be {len(jobs)}.\n"
                        "Do not invent or alter salary values or currencies.\n"
                        "Use only values present in the supplied JSON.\n\n"
                        "Create a structured market analysis from these jobs:\n\n"
                    + json.dumps(jobs, indent=2)
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "market_analysis",
                "strict": True,
                "schema": MarketAnalysis.model_json_schema(),
            },
        },
        max_tokens=5000,
    )

    analysis = MarketAnalysis.model_validate_json(
        response.choices[0].message.content
    )

    # Keep deterministic facts accurate.
    analysis.total_postings = len(jobs)

    # Preserve salary information exactly as extracted.
    analysis.salary_observations = [
        f"{job['job_title']}: {job['salary_range']}"
        for job in jobs
        if job.get("salary_range")
    ]

    ANALYSIS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ANALYSIS_PATH.write_text(
        analysis.model_dump_json(indent=2),
        encoding="utf-8",
    )

    if verbose:
        print(
            "[DEBUG] Market analysis structured validation: passed",
            file=sys.stderr,
        )

    report_response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a detailed but readable Markdown job-market analysis. "
                    "Use headings, bullets, and tables where useful. "
                    "Emphasize concrete counts, salary patterns, experience, "
                    "skills, responsibilities, and company/culture trends. "
                    "Preserve salary values exactly as provided. "
                    "Do not infer currencies, convert hourly wages to annual salaries, "
                    "or calculate compensation that is not explicitly present."
                ),
            },
            {
                "role": "user",
                "content": analysis.model_dump_json(indent=2),
            },
        ],
        max_tokens=4000,
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        report_response.choices[0].message.content,
        encoding="utf-8",
    )

    if verbose:
        print(
            f"[DEBUG] Saved: {ANALYSIS_PATH}",
            file=sys.stderr,
        )
        print(
            f"[DEBUG] Saved: {REPORT_PATH}",
            file=sys.stderr,
        )

    return analysis


if __name__ == "__main__":
    generate_market_analysis(verbose=True)