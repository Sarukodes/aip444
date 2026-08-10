import argparse

from src.llm import set_llm_verbose
from src.market import process_jobs
from src.market_analysis import (
    generate_market_analysis,
)


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Phase 1 - Job Market Analysis"
        )
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
    )

    args = parser.parse_args()

    set_llm_verbose(
        args.verbose
    )

    process_jobs(
        verbose=args.verbose
    )

    generate_market_analysis(
        verbose=args.verbose
    )

    print(
        "Phase 1 complete."
    )


if __name__ == "__main__":
    main()