# Failure Analysis

## Failure 1 — Truncated Structured Output

### What Happened

During Phase 1, some large structured responses were cut off before the JSON was complete.

This happened with the Maarut Senior Full Stack posting and during the Avant Techno Solutions company-research step.

Pydantic rejected the responses because the returned JSON ended unexpectedly.

A similar issue also appeared during Phase 3 testing when an LLM response for structured output was incomplete.

### Why It Happened

The model reached the available output-token limit before completing the structured JSON response.

Larger postings and research results required more output than some of the original limits allowed.

### What I Changed

I increased the output-token limits for larger structured calls.

I also kept the workflows fault-tolerant so that a single failed item would not always stop all remaining work.

Phase 1 also uses skip logic, so when I reran the program, already completed postings did not have to be processed again.

### Result

The failed postings completed successfully after the token limits were increased.

This also showed why Pydantic validation was useful. Incomplete JSON was rejected instead of being silently saved as valid data.


---

## Failure 2 — Market Analysis Hallucinated Deterministic Facts

### What Happened

An early version of the market-analysis report incorrectly stated that 11 postings had been analyzed even though the dataset contained only 10.

The LLM also modified some salary information and made assumptions about currencies and annual compensation.

### Why It Happened

The LLM was being asked to perform both reasoning and deterministic aggregation.

LLMs are useful for identifying patterns and explaining trends, but exact values such as the number of jobs and salary strings can be handled more reliably using Python.

### What I Changed

I moved deterministic information out of the LLM workflow.

The total posting count is now calculated directly in Python:

```python
analysis.total_postings = len(jobs)
```

Salary observations are also copied directly from the structured job data:

```python
analysis.salary_observations = [
    f"{job['job_title']}: {job['salary_range']}"
    for job in jobs
    if job.get("salary_range")
]
```

I also changed the market-report prompt so the model is told not to:

- infer missing currencies
- modify salary values
- convert hourly salaries into annual salaries
- invent compensation information

### Result

The regenerated market analysis correctly used 10 postings and preserved the salary information more accurately.

This showed that deterministic facts are better handled by normal code than by an LLM.


---

## Failure 3 — Excessive Tavily Tool Calls

### What Happened

During Phase 2 and Phase 3 testing, some agent calls generated too many Tavily searches.

In one gap-analysis test, the model wanted to search for many different technologies instead of focusing on one important gap.

During an early Celestica legitimacy run, the context became extremely large because the model requested many searches.

### Why It Happened

The original implementation limited the number of agent rounds, but it did not strictly limit how many tool calls could be requested inside one response.

This meant a small number of agent iterations could still create many external calls.

### What I Changed

I added hard tool-call guardrails.

The final gap-analysis design uses only one focused Tavily search.

The final legitimacy investigation is limited to:

1. one focused Tavily web search
2. one WHOIS lookup

Parallel tool calling was also disabled where appropriate.

Codex later reviewed this implementation and helped enforce the limits.

### Result

The final runs used far fewer external calls and smaller contexts.

Celestica still received a consistent legitimacy result:

**GREEN — 95% confidence**

The system became cheaper, easier to debug, and more predictable.


---

## Failure 4 — Application Advice Could Overstate Experience

### What Happened

An early Phase 3 report produced advice that could make project or academic work sound similar to professional AI/ML experience.

It also suggested technologies that were not clearly supported by the resume.

### Why It Happened

The application-advice prompt initially did not contain strong enough rules about honesty.

Later, Codex found that some honesty instructions were written as standalone Python string literals instead of being included in the actual system prompt.

Because of that, those instructions had no effect on the model.

### What I Changed

The final application-advice prompt explicitly tells the model to:

- never treat academic or project work as professional years of experience
- never recommend claiming unsupported technologies
- recommend learning or building evidence for missing skills
- acknowledge important experience gaps honestly
- never invent candidate achievements

Codex moved these instructions into the actual prompt.

### Result

The final advice is more careful about separating projects, education, and professional experience.

For the Celestica Senior AI Engineer role, the final system identifies the professional experience gap instead of trying to make my projects appear equivalent to senior professional experience.


---

## Weakness 1 — Job Requirement Classification Can Vary

Earlier versions of the job extractor did not always classify required and preferred skills consistently.

Different runs of the same Celestica posting sometimes produced noticeably different numbers of required and preferred skills, which also caused the fit score to change.

### What I Changed

I made two main changes:

- set the extraction temperature to `0`
- made the extraction prompt more specific about required versus preferred skills

The prompt also prevents the exact same skill from being included in both lists.

### Final Result

I ran Celestica twice using the final extractor.

Both runs extracted:

- 20 required skills
- 16 preferred skills

The fit scores were:

- **18% — Growth Target**
- **19% — Growth Target**

Both runs also produced:

**GREEN — 95% confidence**

The one-point difference is much smaller than the variation seen in earlier versions.

A small amount of LLM variation can still occur, but the final implementation is much more consistent.


---

## Weakness 2 — Company Name Ambiguity in Web Search

Company research can sometimes return results for similarly named organizations.

For example, some research for Avant Techno Solutions returned results related to organizations with similar names.

This can introduce irrelevant company information even when the job extraction itself is correct.

A stronger future version could first identify and verify the official company domain, location, or legal company name before accepting external research evidence.


---

## Weakness 3 — PDF Text Extraction Noise

Some job PDFs were created using the browser's Print to PDF feature.

These PDFs can contain unrelated content such as:

- navigation menus
- related-job advertisements
- application controls
- website footer content

This can introduce noise into the text sent to the LLM.

The current system reduces this problem by using structured schemas and telling the model to extract only information supported by the actual posting.

A future version could first detect and isolate the main job-description section before sending the text to the LLM.


---

# Overall Reliability Observations

The system became more reliable when I separated LLM reasoning from deterministic program logic.

The LLM worked well for:

- extracting job information
- identifying market trends
- analyzing resume gaps
- researching companies
- evaluating legitimacy evidence
- generating application advice

Normal Python was more reliable for:

- counting postings
- preserving salary values
- calculating fit percentages
- validating structured data
- controlling tool calls
- enforcing agent limits
- handling files and errors

The evaluation also showed why candidate fit and job legitimacy should remain separate.

A posting can match a candidate's skills well while still being suspicious.

For example, the fake Nexora posting received a high fit score during evaluation, but the legitimacy agent gave it:

**RED — 95% confidence**

This shows that a strong candidate-job match does not mean the employer or posting is trustworthy.

Overall, I would use this application as a job-search decision-support tool rather than treating every result as absolute truth.

Important details such as employer legitimacy, salary, professional-experience requirements, and requests for sensitive personal or financial information should still be manually verified.