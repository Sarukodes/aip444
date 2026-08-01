# AIP444 Lab 9 — Source Credibility Analyzer Agent

This project is a Research Source Credibility Analyzer Agent built with the OpenAI Agents SDK.

Given a webpage URL, the agent:

- reads the source using the Jina Reader API
- investigates the author and publication
- searches for supporting and contradicting evidence using Tavily
- evaluates bias, funding, transparency, and credibility
- records a structured credibility assessment
- saves the final report as a Markdown file

## Features

The agent includes four tools:

- `read_url` — reads webpage content through Jina Reader
- `web_search` — searches the web using Tavily
- `assess_credibility` — records a structured Pydantic credibility evaluation
- `save_report` — saves the final credibility report to the `reports` folder

## Project Structure

```text
lab-09/
├── agent.py
├── tools.py
├── schemas.py
├── SYSTEM_PROMPT.md
├── requirements.txt
├── README.md
└── reports/
    ├── canada_guide_agentic_AI_credibility_report.md
    └── firecrawl-cli-agents-credibility-report.md