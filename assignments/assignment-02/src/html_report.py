from html import escape
from pathlib import Path

from src.schemas import (
    ApplicationAdvice,
    FitAssessment,
    JobPosting,
    LegitimacyAssessment,
)


REPORT_PATH = Path(
    "reports/application-report.html"
)


def e(value) -> str:
    if value is None:
        return "Not listed"

    return escape(
        str(value)
    )


def list_html(items) -> str:
    if not items:
        return "<p>No items identified.</p>"

    return (
        "<ul>"
        + "".join(
            f"<li>{e(item)}</li>"
            for item in items
        )
        + "</ul>"
    )


def legitimacy_signals_html(
    legitimacy:
    LegitimacyAssessment,
) -> str:

    blocks = []

    for signal in legitimacy.signals:

        source = ""

        if (
            signal.source
            and signal.source.startswith(
                ("http://", "https://")
            )
        ):
            source = (
                f'<a href="{e(signal.source)}" '
                'target="_blank">'
                "Source</a>"
            )

        blocks.append(
            f"""
            <div class="signal {e(signal.signal_type)}">
                <strong>{e(signal.signal)}</strong>
                <p>{e(signal.evidence)}</p>
                {source}
            </div>
            """
        )

    return "".join(blocks)


def evidence_html(legitimacy: LegitimacyAssessment) -> str:
    if not legitimacy.evidence:
        return ""

    return "<h3>Evidence Considered</h3>" + list_html(legitimacy.evidence)


def fit_table(
    fit: FitAssessment,
) -> str:

    rows = []

    for match in fit.matches:
        rows.append(
            f"""
            <tr>
                <td>{e(match.category.replace("_", " ").title())}</td>
                <td>{e(match.requirement)}</td>
                <td>
                    <span class="status {e(match.status)}">
                        {e(match.status.upper())}
                    </span>
                </td>
                <td>{e(match.evidence)}</td>
            </tr>
            """
        )

    return "".join(rows)


def resume_adaptation_html(
    advice:
    ApplicationAdvice,
) -> str:

    if not advice.resume_adaptation:
        return "<p>No changes recommended.</p>"

    return "".join(
        f"""
        <div class="card">
            <h3>{e(item.change)}</h3>
            <p>{e(item.reason)}</p>
        </div>
        """
        for item in
        advice.resume_adaptation
    )


def interview_html(
    advice:
    ApplicationAdvice,
) -> str:

    questions = "".join(
        f"""
        <div class="card">
            <h3>{e(item.question)}</h3>
            <p><strong>Why likely:</strong> {e(item.why_likely)}</p>
            <p><strong>Prepare:</strong> {e(item.preparation_tip)}</p>
        </div>
        """
        for item in
        advice.interview_questions
    )

    return (
        questions
        + """
        <h3>Skills to Brush Up On</h3>
        """
        + list_html(
            advice.skills_to_brush_up
        )
        + """
        <h3>Company Research</h3>
        """
        + list_html(
            advice.company_research_topics
        )
        + """
        <h3>Talking Points</h3>
        """
        + list_html(
            advice.talking_points
        )
    )


def write_application_report(
    job: JobPosting,
    legitimacy:
    LegitimacyAssessment,
    fit: FitAssessment,
    advice:
    ApplicationAdvice,
) -> Path:

    verdict_class = (
        legitimacy.verdict.lower()
    )

    warning = ""

    if legitimacy.verdict == "RED":
        warning = """
        <div class="fraud-warning">
            ⚠ This posting contains significant legitimacy concerns.
            Do not submit sensitive personal or financial information
            until the employer has been independently verified.
        </div>
        """

    component_cards = "".join(
        f"""
        <div class="metric">
            <span>{e(name.replace("_", " ").title())}</span>
            <strong>{score}%</strong>
        </div>
        """
        for name, score
        in fit.component_scores.items()
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Application Advisor — {e(job.job_title)}</title>

<style>
* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background: #f5f6f8;
    color: #20242a;
    line-height: 1.55;
}}

header {{
    padding: 46px 8%;
    background: #161b22;
    color: white;
}}

header h1 {{
    margin: 0 0 8px;
    font-size: 34px;
}}

header p {{
    margin: 4px 0;
    opacity: .88;
}}

main {{
    max-width: 1120px;
    margin: 30px auto;
    padding: 0 22px 60px;
}}

section {{
    background: white;
    border-radius: 14px;
    margin: 22px 0;
    padding: 28px;
    box-shadow: 0 3px 16px rgba(0,0,0,.06);
}}

h2 {{
    margin-top: 0;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 12px;
}}

h3 {{
    margin-bottom: 6px;
}}

.verdict {{
    display: inline-block;
    font-weight: 700;
    border-radius: 999px;
    padding: 7px 14px;
}}

.verdict.green {{
    background: #dcfce7;
    color: #166534;
}}

.verdict.yellow {{
    background: #fef3c7;
    color: #92400e;
}}

.verdict.red {{
    background: #fee2e2;
    color: #991b1b;
}}

.signal {{
    border-left: 5px solid #bbb;
    padding: 12px 16px;
    margin: 12px 0;
    background: #fafafa;
}}

.signal.green {{
    border-left-color: #16a34a;
}}

.signal.yellow {{
    border-left-color: #d97706;
}}

.signal.red {{
    border-left-color: #dc2626;
}}

.fraud-warning {{
    background: #991b1b;
    color: white;
    padding: 18px;
    font-weight: 700;
    border-radius: 10px;
    margin: 18px 0;
}}

.score {{
    font-size: 56px;
    font-weight: 800;
    margin: 12px 0 0;
}}

.score-label {{
    font-size: 21px;
    font-weight: 700;
}}

.metrics {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin: 20px 0;
}}

.metric {{
    background: #f4f6f8;
    border-radius: 10px;
    padding: 14px;
}}

.metric span {{
    display: block;
    font-size: 13px;
    color: #6b7280;
}}

.metric strong {{
    font-size: 22px;
}}

table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 14px;
}}

th, td {{
    padding: 11px;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
    vertical-align: top;
}}

th {{
    background: #f8fafc;
}}

.status {{
    font-weight: 700;
}}

.status.met {{
    color: #15803d;
}}

.status.partial {{
    color: #a16207;
}}

.status.missing {{
    color: #b91c1c;
}}

.card {{
    background: #f8fafc;
    padding: 15px 18px;
    margin: 12px 0;
    border-radius: 10px;
}}

a {{
    color: #2563eb;
}}

footer {{
    text-align: center;
    color: #6b7280;
    margin-top: 40px;
}}

@media print {{
    body {{
        background: white;
    }}

    section {{
        box-shadow: none;
        border: 1px solid #ddd;
    }}
}}
</style>
</head>

<body>

<header>
    <h1>{e(job.job_title)}</h1>
    <p>{e(job.company_name)}</p>
    <p>{e(job.location)} · {e(job.remote_status)}</p>
</header>

<main>

{warning}

<section>
    <h2>1. Legitimacy Assessment</h2>

    <span class="verdict {verdict_class}">
        {e(legitimacy.verdict)}
    </span>

    <p>
        <strong>Confidence:</strong>
        {legitimacy.confidence_score}%
    </p>

    <p>{e(legitimacy.recommendation)}</p>

    {legitimacy_signals_html(legitimacy)}
    {evidence_html(legitimacy)}
</section>


<section>
    <h2>2. Fit Assessment</h2>

    <div class="score">{fit.score}%</div>
    <div class="score-label">{e(fit.label)}</div>

    <p>{e(fit.recommendation)}</p>

    <div class="metrics">
        {component_cards}
    </div>

    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Requirement</th>
                <th>Status</th>
                <th>Evidence</th>
            </tr>
        </thead>

        <tbody>
            {fit_table(fit)}
        </tbody>
    </table>
</section>


<section>
    <h2>3. Resume Adaptation</h2>

    {resume_adaptation_html(advice)}
</section>


<section>
    <h2>4. Cover Letter Guidance</h2>

    {list_html(advice.cover_letter_points)}
</section>


<section>
    <h2>5. Interview Prep</h2>

    {interview_html(advice)}
</section>


<footer>
    Generated by AIP444 Assignment 2 Application Advisor
</footer>

</main>

</body>
</html>
"""

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        html,
        encoding="utf-8",
    )

    return REPORT_PATH
