import os
import re
from pathlib import Path
from typing import Any

import requests
from agents import function_tool
from dotenv import load_dotenv
from tavily import TavilyClient

from schemas import CredibilityEvaluation


load_dotenv()

MAX_URL_CONTENT = 10_000
REPORTS_DIRECTORY = Path("reports")


@function_tool
def read_url(url: str) -> str:
    """
    Read a webpage through the Jina Reader API and return its Markdown content.

    Args:
        url: The complete webpage URL to read.
    """
    if not url.startswith(("http://", "https://")):
        return "Error: The URL must begin with http:// or https://."

    reader_url = f"https://r.jina.ai/{url}"

    try:
        response = requests.get(
            reader_url,
            timeout=30,
            headers={"User-Agent": "Source-Credibility-Agent/1.0"},
        )
        response.raise_for_status()

        text = response.text.strip()

        if not text:
            return f"Error: No readable content was returned for {url}."

        if len(text) > MAX_URL_CONTENT:
            text = (
                text[:MAX_URL_CONTENT]
                + "\n\n[Content truncated after 10,000 characters.]"
            )

        return text

    except requests.Timeout:
        return f"Error: Reading {url} timed out."

    except requests.RequestException as error:
        return f"Error: Could not read {url}. Details: {error}"


@function_tool
def web_search(query: str) -> dict[str, Any]:
    """
    Search the web using Tavily.

    Use this tool to investigate authors, publications, claims,
    corroborating evidence, contradictions, and fact-checks.

    Args:
        query: A focused web-search query.
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "TAVILY_API_KEY was not found in the environment.",
        }

    try:
        client = TavilyClient(api_key=api_key)

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )

        cleaned_results = []

        for result in response.get("results", []):
            cleaned_results.append(
                {
                    "title": result.get("title", "Unknown title"),
                    "url": result.get("url", "Unknown URL"),
                    "content": result.get("content", ""),
                    "score": result.get("score"),
                }
            )

        return {
            "status": "success",
            "query": query,
            "answer": response.get("answer"),
            "results": cleaned_results,
        }

    except Exception as error:
        return {
            "status": "error",
            "query": query,
            "message": f"Web search failed: {error}",
        }


@function_tool
def assess_credibility(
    evaluation: CredibilityEvaluation,
) -> dict[str, Any]:
    """
    Record a complete structured credibility assessment.

    This tool has no external side effects. It forces the agent to organize
    its evidence and reasoning before writing the final report.

    Args:
        evaluation: The completed credibility evaluation based only on
            information discovered during the investigation.
    """
    return {
        "status": "evaluation_recorded",
        "evaluation": evaluation.model_dump(mode="json"),
    }


@function_tool
def save_report(filename: str, markdown_content: str) -> dict[str, str]:
    """
    Save the final credibility report as a Markdown file.

    Args:
        filename: The report filename, such as canada_source_report.md.
        markdown_content: The complete Markdown report.
    """
    safe_filename = Path(filename).name

    if not safe_filename:
        return {
            "status": "error",
            "message": "A valid filename is required.",
        }

    safe_filename = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        safe_filename,
    )

    if not safe_filename.lower().endswith(".md"):
        safe_filename += ".md"

    try:
        REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)

        report_path = REPORTS_DIRECTORY / safe_filename
        report_path.write_text(markdown_content, encoding="utf-8")

        return {
            "status": "success",
            "message": "Credibility report saved successfully.",
            "path": str(report_path),
        }

    except OSError as error:
        return {
            "status": "error",
            "message": f"Could not save the report: {error}",
        }