import argparse
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


STUDENT_NAME = "Saru Koirala"
STUDENT_ID = "188083232"


def print_header():
    print("=" * 60)
    print("Lab 2: ACE Flashcard Generator")
    print(f"Name: {STUDENT_NAME}")
    print(f"Student ID: {STUDENT_ID}")
    print("=" * 60)
    print()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate ACE flashcards from course notes"
    )

    parser.add_argument("notes_path", help="Path to notes file")

    parser.add_argument(
        "--cards",
        type=int,
        default=3,
        help="Number of flashcards to generate (1-5)"
    )

    args = parser.parse_args()

    if args.cards < 1 or args.cards > 5:
        parser.error("--cards must be between 1 and 5")

    return args


def get_file_contents(path, description):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    except FileNotFoundError:
        print(f"❌ Error: {description} not found: {path}")
        sys.exit(1)

    except Exception as error:
        print(f"❌ Error reading {description}: {path}")
        print(error)
        sys.exit(1)


def validate_api_key():
    load_dotenv(dotenv_path=Path("../../.env"))

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY missing in .env")
        sys.exit(1)

    return api_key


def build_user_prompt(notes_content, cards):
    return f"""
Generate exactly {cards} ACE flashcards from the notes below.

STRICT OUTPUT RULES:
- Start directly with === CARD 1 ===
- Then continue with === CARD 2 ===, === CARD 3 ===, etc.
- If {cards} cards are requested, output CARD 1 through CARD {cards}.
- Generate exactly {cards} cards.
- Use ONLY the provided notes.
- Do NOT hallucinate.
- EVIDENCE must be a direct quote from the notes.
- Expand all acronyms in the CHALLENGE field.
- MISCONCEPTION must sound like a confused student quote.
- Use these exact field names only:
APPLICATION:
CHALLENGE:
ANSWER:
EVIDENCE:
MISCONCEPTION:
CORRECTION:
- Do NOT use markdown formatting.
- Do NOT write **Flashcard**.
- Do NOT skip CARD 1.

<course_notes>
{notes_content}
</course_notes>
"""


def call_openrouter(api_key, system_prompt, user_prompt):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )

        return response.choices[0].message.content

    except Exception as error:
        print("❌ Error calling OpenRouter API")
        print(error)
        sys.exit(1)


def extract_cards(output):
    return re.findall(
        r"(=== CARD \d+ ===.*?)(?=\n=== CARD \d+ ===|\Z)",
        output,
        re.DOTALL
    )


def main():
    print_header()

    args = parse_arguments()
    api_key = validate_api_key()

    system_prompt = get_file_contents(
        "SYSTEM_PROMPT.md",
        "System prompt file"
    )

    notes_content = get_file_contents(
        args.notes_path,
        "Notes file"
    )

    if not notes_content.strip():
        print("❌ Error: Notes file is empty.")
        sys.exit(1)

    user_prompt = build_user_prompt(notes_content, args.cards)

    cards = []
    output = ""

    for attempt in range(3):
        output = call_openrouter(api_key, system_prompt, user_prompt)
        cards = extract_cards(output)

        if len(cards) == args.cards:
            break

    if not cards or len(cards) != args.cards:
        print("❌ Could not generate the requested number of ACE cards.")
        print(f"Requested: {args.cards}")
        print(f"Generated: {len(cards)}")
        print()
        print(output)
        sys.exit(1)

    print(f"✅ Generated {len(cards)} flashcard(s):")
    print()

    for card in cards:
        print(card.strip())
        print()


if __name__ == "__main__":
    main()