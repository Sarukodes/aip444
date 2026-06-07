import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from schemas import FlashcardResponse

load_dotenv(dotenv_path=Path("../../.env"))

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

async def generate_flashcards(notes: str, cards: int) -> FlashcardResponse:
    if not os.getenv("OPENROUTER_API_KEY"):
        raise ValueError("OPENROUTER_API_KEY missing in .env")

    with open("SYSTEM_PROMPT.md", "r", encoding="utf-8") as file:
        system_prompt = file.read()

    completion = client.beta.chat.completions.parse(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Generate exactly {cards} ACE flashcards from these notes:\n\n{notes}",
            },
        ],
        temperature=0.1,
        response_format=FlashcardResponse,
    )

    return completion.choices[0].message.parsed