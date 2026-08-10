# Extraction Spot-Check

## Posting 1 — Junior Software Developer - Observability — Canonical

| Field | Expected | Extracted | Correct? |
| :--- | :--- | :--- | :--- |
| Job title | Junior Software Developer - Observability | Junior Software Developer - Observability | ✅ |
| Company | Canonical | Canonical | ✅ |
| Location | Toronto / Americas region | Toronto | ✅ |
| Remote status | Home based / remote | Home based | ✅ |
| Posting age | No posting date visible | null | ✅ |
| Required skills | Python and Go | Python, Go | ✅ |
| Education | Bachelor's or equivalent in Computer Science, STEM, or similar field | Bachelor's or equivalent in Computer Science, STEM, or similar degree | ✅ |
| Salary | Not listed | null | ✅ |
| Responsibilities | Write, test, and document code; debug issues; review code; collaborate with team members | Extracted these responsibilities correctly | ✅ |

### Observations

The Canonical extraction was accurate and conservative.

The system correctly returned `null` when salary and posting date were not available instead of inventing values.

The main area requiring interpretation was deciding whether technologies such as Linux, Kubernetes, observability, and distributed systems belonged under required or preferred skills. Overall, the structured extraction matched the source posting well.


---

## Posting 2 — Software Developer — Avant Techno Solutions

| Field | Expected | Extracted | Correct? |
| :--- | :--- | :--- | :--- |
| Job title | Software developer | Software developer | ✅ |
| Company | Avant Techno Solutions | Avant Techno Solutions | ✅ |
| Location | Toronto, ON | Toronto, ON | ✅ |
| Remote status | On site | On site | ✅ |
| Posting date | Posted July 29, 2026 | Posted on July 29, 2026 | ✅ |
| Posting age | About 8 days at capture time | 8 days | ✅ |
| Salary | 50.43 hourly | 50.43 hourly | ✅ |
| Education | Bachelor's degree or equivalent experience | Bachelor's degree or equivalent experience | ✅ |
| Experience | 3 years to less than 5 years | 3 years to less than 5 years | ✅ |
| Required technologies | C, Java, SQL, JSON | C, Java, SQL, JavaScript Object Notation (JSON) | ✅ |
| Preferred skill | Robotic process automation | Robotic process automation | ✅ |

### Responsibilities Spot-Check

The extractor correctly identified responsibilities including:

- writing, modifying, integrating, and testing software code
- maintaining existing programs
- communicating technical problems and solutions
- documenting software operation and maintenance
- assisting with user requirements
- researching and evaluating software products
- supporting e-commerce and Internet applications
- managing incidents
- providing post-sale client support

### Observations

The Avant posting was especially useful for evaluation because the Job Bank source contains clearly defined fields such as salary, work location, experience, education, and posting date.

The structured extraction matched these fields very closely.

One weakness appeared in the separate company-research portion. Some search results referred to organizations named **Avant Technologies** rather than **Avant Techno Solutions**. This shows that company-name ambiguity can introduce unrelated web-search evidence even when the original job extraction itself is accurate.

A stronger future version could verify the company domain or location before accepting company-research results.


# Overall Extraction Assessment

The two manual spot-checks show that the structured job extractor performs well on both:

- a relatively clean company-careers posting
- a structured Job Bank posting

The strongest behavior was explicit handling of missing information. The system did not invent salary or posting-date values when those fields were absent.

The main remaining weakness is not the core PDF extraction itself, but ambiguity during external company research when similarly named organizations appear in search results.