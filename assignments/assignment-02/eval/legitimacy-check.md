# Legitimacy Agent Evaluation

## Test 1 — Clearly Legitimate Posting

### Posting

Senior AI Engineer, IT Solutions — Celestica International LP

### Signals Found

Green signals included:

- established company presence
- official company website and careers page
- matching company domain
- long-established domain registration
- realistic salary range
- detailed and specific job description
- job information consistent with Celestica's company profile

### WHOIS Result

The legitimacy agent performed a WHOIS lookup on:

`celestica.com`

The domain was registered on January 3, 1996.

Registrar:

`CSC Corporate Domains, Inc.`

The long domain history supported the legitimacy assessment.

### Verdict

**GREEN**

Confidence:

**95%**

### Do I Agree?

Yes.

Celestica has an established company presence, an official careers website, a long-standing domain, and a detailed job posting.

The job information and salary were also consistent with a real senior AI engineering opportunity.

The agent correctly treated these factors as positive legitimacy evidence.


---

## Test 2 — Deliberately Suspicious Posting

### Posting

Junior AI Engineer — Nexora AI Solutions

For this evaluation I created a deliberately suspicious posting containing multiple common scam signals.

The posting included:

- a salary of $280,000 CAD for a junior role requiring no experience
- interviews conducted only through Telegram
- a Gmail recruiter address
- a request for Social Insurance Number
- a request for banking information
- a request for photo ID and home address before the interview
- a $750 refundable equipment and training deposit
- a fake `.example` company domain
- pressure to respond within 24 hours


### Web and WHOIS Investigation

The system searched for an official Nexora AI Solutions company presence.

It also attempted a WHOIS lookup on:

`nexora-ai.example`

The WHOIS lookup failed because no valid registration information was available for the domain.


### Signals Found

The legitimacy agent identified the following red signals:

- **Unrealistically high salary for a junior role**
- **Suspicious application process requesting sensitive information and upfront fees**
- **Interviews conducted exclusively through Telegram**
- **Placeholder or non-existent company website**
- **Artificial urgency to apply quickly**

The agent also identified yellow signals involving conflicting or unverifiable company information.


### Verdict

**RED**

Confidence:

**95%**

### Do I Agree?

Yes.

The result is appropriate because the posting contains several classic recruitment-scam indicators.

The strongest warning signs are the request for sensitive financial and identity information before an interview, the upfront $750 payment, the Telegram-only communication, and the unverifiable domain.

Any one of these would justify additional caution. Together, they strongly support a RED verdict.


# Fit vs Legitimacy Observation

An interesting result occurred during this test.

The fake posting received:

**100% — Strong Fit**

because its technical and education requirements were intentionally very easy for the candidate to satisfy.

However, its legitimacy result was:

**RED — 95% confidence**

This demonstrates why fit and legitimacy should be evaluated separately.

A job can appear to match a candidate extremely well while still being unsafe or fraudulent.

The application should therefore never treat a high fit score as evidence that a posting is legitimate.


# Overall Assessment

The legitimacy agent successfully distinguished between the two test cases:

- **Celestica — GREEN, 95% confidence**
- **Nexora AI Solutions fake posting — RED, 95% confidence**

The combination of Tavily web research, WHOIS investigation, posting-content analysis, and structured red/yellow/green signals produced useful and understandable results.

One limitation is that WHOIS information may sometimes be unavailable or privacy protected. The system therefore does not treat missing WHOIS registrant information alone as evidence of fraud.

The legitimacy result should be used as decision support rather than absolute proof, but the evaluation shows that the agent can identify both strong legitimacy signals and obvious recruitment-scam patterns.