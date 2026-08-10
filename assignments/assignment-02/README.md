# AIP444 Assignment 2 - Job Search Assistant

This project is a Job Search Assistant for AIP444 Assignment 2.

It analyzes job postings, creates a market analysis, compares my resume with the market, and gives advice for a new job posting. It also checks the legitimacy of the new posting using web search and WHOIS.

The project is written in Python and all LLM calls are made through OpenRouter.

---

## Setup

### 1. Go to the assignment folder

```bash
cd ~/Desktop/seneca/AIP/aip444/assignments/assignment-02
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it in Git Bash:

```bash
source .venv/Scripts/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The main dependencies used in this project are:

```text
openai
pydantic
python-dotenv
pypdf
tavily-python
python-whois
```

---

## Environment Variables

The project requires an OpenRouter API key and a Tavily API key.

The `.env.example` file contains:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

My actual `.env` file is stored in the main `aip444` folder.

The program checks both:

```text
aip444/.env
```

and:

```text
assignments/assignment-02/.env
```

The real `.env` file should not be committed to GitHub.

---

## Input Files

Raw job posting PDFs and my resume are kept locally and are not required to be committed.

For Phase 1, job posting PDFs are placed in:

```text
inputs/jobs/
```

For Phase 2, my resume is stored as:

```text
inputs/resume/resume.pdf
```

For Phase 3, the new job posting is provided as a command-line argument.

Example:

```text
inputs/new-job.pdf
```

---

# Phase 1 - Job Market Analysis

Phase 1 processes the original job posting PDFs.

I used 10 real job postings.

For each posting, the program extracts structured information such as:

- job title
- company
- location
- remote status
- posting age
- required skills
- preferred skills
- experience
- education
- salary
- responsibilities

Pydantic is used to validate the structured LLM output.

The program also gives the LLM access to a Tavily web search tool for company research.

## Run Phase 1

```bash
python -m src.phase1 --verbose
```

Phase 1 saves one JSON file for each posting in:

```text
data/jobs/
```

It also generates:

```text
data/analysis/market-analysis.json
reports/market-analysis.md
```

Phase 1 can be run again when new jobs are added.

If a posting has already been processed, the existing JSON file is detected and the posting is skipped instead of being processed again.

---

# Phase 2 - Resume Gap Analysis

Phase 2 parses my resume and compares it with the market data created in Phase 1.

The resume extraction includes:

- hard skills
- soft skills
- work experience
- education
- certifications and training
- projects and accomplishments
- domain keywords

## Run Phase 2

```bash
python -m src.phase2 inputs/resume/resume.pdf --verbose
```

The structured resume is saved to:

```text
data/resume/resume.json
```

The program then compares the resume with the market analysis and identifies:

- strengths
- gaps
- unique value

Each gap is placed into one of these levels:

```text
Quick win
Short-term
Medium-term
Long-term
```

Tavily search is used when extra research is needed for a recommendation.

Phase 2 generates:

```text
data/analysis/gap-analysis.json
reports/gap-analysis.md
```

---

# Phase 3 - Application Advisor

Phase 3 takes a new job posting that was not part of the original Phase 1 job set.

It reuses the Phase 1 extraction and web search code and loads the resume and market information from the earlier phases.

It performs:

- structured extraction of the new posting
- company research
- legitimacy assessment
- WHOIS lookup
- resume/job fit scoring
- resume adaptation suggestions
- cover letter guidance
- interview preparation

## Run Phase 3

```bash
python -m src.advisor inputs/new-job.pdf --verbose
```

The final report is saved to:

```text
reports/application-report.html
```

The report contains the required five sections:

1. Legitimacy Assessment
2. Fit Assessment
3. Resume Adaptation
4. Cover Letter Guidance
5. Interview Prep

---

## Legitimacy Assessment

The legitimacy agent uses:

- Tavily web search
- WHOIS lookup

The WHOIS tool checks information such as:

- domain registration date
- expiration date
- registrar
- registrant organization when available
- country

The legitimacy result is returned as:

```text
GREEN
YELLOW
RED
```

The assessment also includes the evidence found and a recommendation.

To control cost, the legitimacy investigation has a limited number of tool calls.

---

## Fit Scoring

The fit score checks:

- required skills
- preferred skills
- experience
- education

Requirements can be classified as:

```text
met
partial
missing
```

The score is calculated in Python after the individual requirements are evaluated.

The scoring ranges are:

```text
80-100% = Strong Fit
50-79%  = Good Fit
30-49%  = Stretch
0-29%   = Growth Target
```

Fit scoring and legitimacy are kept separate because a posting can match a candidate well while still being suspicious.

---

# Verbose Mode

All three phases support:

```bash
--verbose
```

Examples:

```bash
python -m src.phase1 --verbose
```

```bash
python -m src.phase2 inputs/resume/resume.pdf --verbose
```

```bash
python -m src.advisor inputs/new-job.pdf --verbose
```

Verbose mode shows information such as:

- LLM calls
- token usage
- extraction steps
- structured output validation
- Tavily tool calls
- WHOIS calls
- fit scoring
- legitimacy signals

Debug information is written to `stderr`.

---

# Running the Evaluation

The evaluation results are stored in:

```text
eval/extraction-spot-check.md
eval/scoring-check.md
eval/legitimacy-check.md
eval/failure-analysis.md
```

## Extraction Spot Check

Two Phase 1 job postings were manually compared with their extracted JSON results.

The results are documented in:

```text
eval/extraction-spot-check.md
```

## Scoring Check

Phase 3 was run on postings with different expected fit levels.

To run a scoring test:

```bash
python -m src.advisor <job-posting.pdf> --verbose
```

The scores and consistency results are documented in:

```text
eval/scoring-check.md
```

## Legitimacy Check

The legitimacy agent was tested using:

- a legitimate Celestica posting
- a deliberately fake Nexora AI Solutions posting

Run the advisor with each evaluation posting:

```bash
python -m src.advisor <job-posting.pdf> --verbose
```

The results are documented in:

```text
eval/legitimacy-check.md
```

## Failure Analysis

Failures and weaknesses found during development and testing are documented in:

```text
eval/failure-analysis.md
```

---

# Output Files

The generated files required by the assignment are:

```text
data/jobs/*.json

data/resume/resume.json

data/analysis/market-analysis.json
data/analysis/gap-analysis.json

reports/market-analysis.md
reports/gap-analysis.md
reports/application-report.html

eval/extraction-spot-check.md
eval/scoring-check.md
eval/legitimacy-check.md
eval/failure-analysis.md

docs/reflection.md
```

---

# Extras / Additional Features

I added a few features beyond the basic processing:

- `--verbose` debug logging
- Phase 1 skip logic
- Tavily company research
- WHOIS domain checking
- GREEN/YELLOW/RED legitimacy assessment
- deterministic fit score calculation
- hard limits on agent tool calls to control cost
- graceful handling of Tavily and WHOIS failures
- single-file HTML application report

Phase 3 was developed and reviewed using Codex as the coding agent.

The coding-agent process is discussed in:

```text
docs/reflection.md
```