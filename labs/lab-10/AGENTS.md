# AGENTS.md

## Project

A utility library for encoding and decoding media files
as Base64 Data URIs. Supports common image, audio, and
video formats.

## Tech Stack

- Python with type hints
- Pydantic for validation
- pytest for testing

## Structure

- `src/` — Library source code
- `tests/` — Test files
- `tests/fixtures/` — Small sample media files for testing

## Commands

- `pytest` — Run all tests

## Conventions

- All public functions must have docstring comments
- All exported types must use Pydantic models
- Handle errors explicitly — never silently swallow failures
- Run tests before considering any task complete
- Keep functions small and focused — one job per function