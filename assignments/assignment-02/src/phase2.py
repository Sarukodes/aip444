import argparse

from src.gap_analysis import (
    generate_gap_analysis,
)
from src.llm import set_llm_verbose
from src.resume_extractor import (
    extract_resume,
    save_resume,
)


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Phase 2 - Resume Gap Analysis"
        )
    )

    parser.add_argument(
        "resume",
        nargs="?",
        default="inputs/resume/resume.pdf",
        help="Path to resume PDF",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
    )

    args = parser.parse_args()

    set_llm_verbose(
        args.verbose
    )

    resume = extract_resume(
        args.resume,
        verbose=args.verbose,
    )

    save_resume(
        resume
    )

    generate_gap_analysis(
        verbose=args.verbose,
    )

    print(
        "Phase 2 complete."
    )


if __name__ == "__main__":
    main()