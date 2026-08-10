# Phase 3 Codex Initial Prompt

I am working on AIP444 Assignment 2 in an existing Python project.

Before changing anything, inspect the existing Phase 1 and Phase 2 code under `src/`.

Phase 1 already provides:

- PDF job extraction
- Pydantic structured outputs
- OpenRouter client
- Tavily web search
- company research
- market analysis
- verbose logging

Phase 2 already provides:

- resume PDF extraction
- structured resume data
- market-vs-resume gap analysis
- Tavily research
- gap-analysis JSON and Markdown report

Build Phase 3 primarily by reusing the existing code rather than rewriting Phase 1 or Phase 2.

Phase 3 must accept a new job posting PDF and generate:

`reports/application-report.html`

The report must contain these sections in this order:

1. Legitimacy Assessment
2. Fit Assessment
3. Resume Adaptation
4. Cover Letter Guidance
5. Interview Prep

Requirements:

- Reuse Phase 1 job extraction.
- Load:
  - `data/resume/resume.json`
  - `data/analysis/market-analysis.json`
  - `data/analysis/gap-analysis.json`
- Research the new company using the existing Tavily web search.
- Implement a WHOIS lookup tool using `python-whois`.
- Create a legitimacy assessment using both web search and WHOIS.
- The legitimacy result must be structured and contain:
  - verdict
  - confidence
  - green/red/yellow signals
  - evidence
  - recommendation
- Do not treat WHOIS privacy protection itself as fraud.
- Fit scoring must be explainable.
- Give credit for partial matches.
- The system should encourage reasonable candidates to apply instead of requiring 100% of qualifications.
- Resume recommendations must be specific to the posting.
- Never invent candidate experience.
- Cover letter guidance must be company/job specific.
- Interview preparation must include:
  - likely questions
  - skills to review
  - company research topics
  - candidate talking points
- HTML and CSS must exist in one HTML file.
- The program must support `--verbose`.
- Debug logs must go to stderr.
- Log tool calls, legitimacy signals, fit scoring, and LLM token usage where possible.
- Handle failed research/WHOIS gracefully.
- Use hard limits on agent/tool loops.
- All LLM calls must continue using OpenRouter.
- Do not expose API keys.

Preferred Phase 3 command:

`python -m src.advisor path/to/new-posting.pdf --verbose`

After implementing it, run basic import/tests and review your own implementation against the requirements above. Fix any obvious failures before stopping.