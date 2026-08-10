import argparse
import json
import sys
from pathlib import Path

from src.advice_generator import (
    generate_application_advice,
)
from src.company_research import (
    research_company,
)
from src.fit_scoring import assess_fit
from src.html_report import (
    write_application_report,
)
from src.job_extractor import extract_job
from src.legitimacy_agent import (
    assess_legitimacy,
)
from src.llm import set_llm_verbose
from src.pdf_utils import extract_pdf_text
from src.schemas import (
    CompanyResearch,
    LegitimacyAssessment,
    LegitimacySignal,
)


RESUME_PATH = Path(
    "data/resume/resume.json"
)

MARKET_PATH = Path(
    "data/analysis/market-analysis.json"
)

GAP_PATH = Path(
    "data/analysis/gap-analysis.json"
)


def load_json(path: Path):
    if not path.exists():
        raise RuntimeError(
            f"Required Phase 1/2 file missing: {path}"
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def empty_company_research():
    return CompanyResearch(
        company_size=None,
        industry=None,
        recent_news=[],
        culture_signals=[],
        additional_context=[],
        sources=[],
    )


def unavailable_legitimacy_assessment() -> LegitimacyAssessment:
    """Return a cautious result when external investigation cannot finish."""
    return LegitimacyAssessment(
        verdict="YELLOW",
        confidence_score=0,
        signals=[
            LegitimacySignal(
                signal_type="yellow",
                signal="Legitimacy investigation incomplete",
                evidence=(
                    "Automated web/WHOIS investigation could not be completed; "
                    "this is not evidence that the employer is fraudulent."
                ),
                source=None,
            )
        ],
        evidence=[],
        recommendation=(
            "Verify the employer through its official website or a known contact "
            "before sharing sensitive information."
        ),
    )


def run_advisor(
    posting_pdf: str,
    verbose: bool = False,
):

    set_llm_verbose(verbose)

    pdf_path = Path(
        posting_pdf
    )

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Posting PDF not found: {posting_pdf}"
        )

    if verbose:
        print(
            "[DEBUG] Phase 3 starting",
            file=sys.stderr,
        )

    resume = load_json(
        RESUME_PATH
    )

    market = load_json(
        MARKET_PATH
    )

    gaps = load_json(
        GAP_PATH
    )

    posting_text = extract_pdf_text(
        str(pdf_path)
    )

    job = extract_job(
        str(pdf_path),
        verbose=verbose,
    )

    try:
        research = research_company(
            job.company_name,
            job.job_title,
            verbose=verbose,
        )

    except Exception as exc:
        research = (
            empty_company_research()
        )

        if verbose:
            print(
                "[DEBUG] Company research failed; "
                f"continuing without it: {exc}",
                file=sys.stderr,
            )

    job.company_research = research

    try:
        legitimacy = assess_legitimacy(
            job,
            posting_text,
            market,
            verbose=verbose,
        )
    except Exception as exc:
        legitimacy = unavailable_legitimacy_assessment()
        if verbose:
            print(
                "[DEBUG] Legitimacy assessment failed; "
                f"continuing with an inconclusive result: {exc}",
                file=sys.stderr,
            )

    fit = assess_fit(
        job,
        resume,
        verbose=verbose,
    )

    advice = (
        generate_application_advice(
            job,
            resume,
            market,
            gaps,
            fit,
            legitimacy,
        )
    )

    report_path = (
        write_application_report(
            job,
            legitimacy,
            fit,
            advice,
        )
    )

    if verbose:
        print(
            "[DEBUG] Phase 3 completed",
            file=sys.stderr,
        )

    print(
        f"Application report generated: {report_path}"
    )

    print(
        f"Fit score: {fit.score}% ({fit.label})"
    )

    print(
        "Legitimacy: "
        f"{legitimacy.verdict} "
        f"({legitimacy.confidence_score}% confidence)"
    )

    return {
        "job": job,
        "legitimacy": legitimacy,
        "fit": fit,
        "advice": advice,
    }


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Phase 3 - Application Advisor"
        )
    )

    parser.add_argument(
        "posting_pdf",
        help=(
            "Path to a new job posting PDF "
            "not used in Phase 1"
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed debug logging",
    )

    args = parser.parse_args()

    run_advisor(
        args.posting_pdf,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
