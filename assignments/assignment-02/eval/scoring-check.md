# Phase 3 Scoring Check

## Posting 1 — Magical New Grad Software Engineer

### Expected Fit

I expected this posting to be a strong fit because it is designed for new graduates and its requirements are much closer to my current education, programming skills, and project experience.

The role does not require the same level of professional experience as a senior position.

### System Result

The final run produced:

**84% — Strong Fit** 

Scoring breakdown:

- Required skills: 83%
- Preferred skills: 64%
- Experience: 100%
- Education: 100%

### Do I Agree?

Yes. I agree with the Strong Fit result.

This role is much closer to my current background because I have relevant education, programming experience, AI-related projects, API work, and other software development skills.

I do not match every preferred skill, but the scoring system gives partial credit instead of requiring a perfect match.

### Did the System Encourage Applying?

Yes.

The system treated the missing preferred skills as areas I could improve instead of using them as a reason not to apply.

For a new-grad role with an 84% score, the Strong Fit recommendation appropriately encourages applying.


---

## Posting 2 — Celestica Senior AI Engineer

### Expected Fit

I expected this posting to be a weak fit or a growth target.

Although I have some related programming, API, AI, and project experience, this is a Senior AI Engineer role and requires significantly more professional AI/software engineering experience than I currently have.

The biggest expected gap was senior-level professional experience.

### System Result

The final run produced:

**19% — Growth Target**

Scoring breakdown:

- Required skills: 22%
- Preferred skills: 6%
- Experience: 0%
- Education: 50%

### Do I Agree?

Yes. I agree with this assessment.

I have some transferable technical skills and projects, but I do not yet have the professional experience expected for a Senior AI Engineer position.

The Growth Target result makes sense because this role shows the skills and experience I would need to build for similar senior positions in the future.

### Did the System Encourage Applying?

The system did not simply say that I was unqualified.

Because the score was below 30%, it classified the role as a Growth Target rather than an immediate strong application opportunity.

I think this is reasonable because the professional experience gap is significant, while the report can still help identify what I would need to learn or improve.


---

# Consistency Check

I ran the Celestica Senior AI Engineer posting twice using the final version of the job extractor.

## Run 1

- Required skills extracted: 20
- Preferred skills extracted: 16
- Fit score: **18%**
- Recommendation: **Growth Target**
- Legitimacy: **GREEN — 95% confidence**

## Run 2

- Required skills extracted: 20
- Preferred skills extracted: 16
- Fit score: **19%**
- Recommendation: **Growth Target**
- Legitimacy: **GREEN — 95% confidence**

### Consistency Result

The final two runs were very consistent.

Both runs extracted the same number of required and preferred skills and produced the same Growth Target recommendation.

The fit score changed by only one percentage point, from 18% to 19%.

The legitimacy result was also the same in both runs:

**GREEN — 95% confidence**

I consider this amount of variation acceptable for an LLM-based system.

Earlier versions of the extractor showed more variation. To improve consistency, I set the extraction temperature to `0` and made the prompt more specific about how required and preferred skills should be classified.


# Overall Scoring Observation

The final scoring system produced clearly different results for jobs at different career levels:

- **Magical New Grad Software Engineer: 84% — Strong Fit**
- **Celestica Senior AI Engineer: 19% — Growth Target**

These results match what I expected based on my current background.

The system also gives partial credit for requirements instead of expecting a candidate to match every qualification.

This makes the scoring more useful because it encourages applying when the candidate has a reasonable match while still identifying roles that are better treated as future growth targets.