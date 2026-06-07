from pydantic import BaseModel, Field
from typing import List


class Flashcard(BaseModel):
    application: str = Field(
        description="1-2 sentence real-world workplace task"
    )
    challenge: str = Field(
        description="Specific problem to solve"
    )
    answer: str = Field(
        description="Correct solution"
    )
    evidence: str = Field(
        description="Direct quote from notes"
    )
    misconception: str = Field(
        description="Incorrect student belief"
    )
    correction: str = Field(
        description="Why misconception is wrong"
    )


class FlashcardResponse(BaseModel):
    flashcards: List[Flashcard]