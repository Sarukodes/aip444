import argparse
import re
import sys
from pathlib import Path

from src.company_research import research_company
from src.job_extractor import extract_job, save_job


INPUT_DIR = Path("inputs/jobs")
OUTPUT_DIR = Path("data/jobs")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def process_jobs(verbose: bool = False) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(INPUT_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No job PDFs found in inputs/jobs/")
        return

    for pdf_path in pdf_files:
        slug = slugify(pdf_path.stem)
        output_path = OUTPUT_DIR / f"{slug}.json"

        if output_path.exists():
            if verbose:
                print(
                    f"[DEBUG] Skipping already processed posting: {pdf_path.name}",
                    file=sys.stderr,
                )
            continue

        try:
            if verbose:
                print(
                    f"[DEBUG] Processing new posting: {pdf_path.name}",
                    file=sys.stderr,
                )

            job = extract_job(str(pdf_path), verbose=verbose)

            research = research_company(
                job.company_name,
                job.job_title,
                verbose=verbose,
            )

            job.company_research = research

            save_job(job, str(output_path))

            print(f"Processed: {pdf_path.name}")
            print(f"Saved: {output_path}")

        except Exception as exc:
            print(
                f"Failed to process {pdf_path.name}: {exc}",
                file=sys.stderr,
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 1 - Job Market Analysis"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed debug logging",
    )

    args = parser.parse_args()

    process_jobs(verbose=args.verbose)


if __name__ == "__main__":
    main()