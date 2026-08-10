from typing import Literal, Optional

from pydantic import BaseModel, Field


# ============================================================
# PHASE 1
# ============================================================


class CompanyResearch(BaseModel):
    company_size: Optional[str]
    industry: Optional[str]
    recent_news: list[str]
    culture_signals: list[str]
    additional_context: list[str]
    sources: list[str]


class JobPosting(BaseModel):
    job_title: str
    company_name: str

    location: Optional[str]
    remote_status: Optional[str]

    posting_age_days: Optional[int]
    posting_date_text: Optional[str]

    required_skills: list[str]
    preferred_skills: list[str]

    experience_level: Optional[str]
    education_requirements: Optional[str]

    salary_range: Optional[str]

    key_responsibilities: list[str]

    company_research: Optional[CompanyResearch]


class SkillFrequency(BaseModel):
    skill: str
    count: int


class MarketAnalysis(BaseModel):
    total_postings: int
    common_required_skills: list[SkillFrequency]
    common_preferred_skills: list[SkillFrequency]

    experience_patterns: list[str]
    education_patterns: list[str]
    salary_observations: list[str]

    common_responsibilities: list[str]
    industry_trends: list[str]
    culture_expectations: list[str]
    notable_trends: list[str]


# ============================================================
# PHASE 2
# ============================================================


class WorkExperience(BaseModel):
    role: str
    company: str
    duration: Optional[str]
    responsibilities: list[str]
    achievements: list[str]


class Education(BaseModel):
    degree: str
    institution: str
    details: list[str]


class ResumeData(BaseModel):
    hard_skills: list[str]
    soft_skills: list[str]

    work_experience: list[WorkExperience]
    education: list[Education]

    certifications_training: list[str]
    projects_accomplishments: list[str]

    keywords_domain_expertise: list[str]


GapLevel = Literal[
    "Quick win",
    "Short-term",
    "Medium-term",
    "Long-term",
]


class GapItem(BaseModel):
    gap: str
    level: GapLevel

    reason: str
    action: str

    research_sources: list[str]


class GapAnalysis(BaseModel):
    strengths: list[str]
    gaps: list[GapItem]

    unique_value: list[str]
    overall_observations: list[str]


# ============================================================
# PHASE 3 - LEGITIMACY
# ============================================================


SignalType = Literal[
    "green",
    "yellow",
    "red",
]


class LegitimacySignal(BaseModel):
    signal_type: SignalType
    signal: str
    evidence: str
    source: Optional[str]


class LegitimacyAssessment(BaseModel):
    verdict: Literal[
        "GREEN",
        "YELLOW",
        "RED",
    ]

    confidence_score: int = Field(
        ge=0,
        le=100,
    )

    signals: list[LegitimacySignal]
    evidence: list[str] = Field(
        default_factory=list,
        description="Concise, source-backed facts used to reach the verdict.",
    )
    recommendation: str


# ============================================================
# PHASE 3 - FIT
# ============================================================


RequirementStatus = Literal[
    "met",
    "partial",
    "missing",
]


RequirementCategory = Literal[
    "required_skill",
    "preferred_skill",
    "experience",
    "education",
]


class RequirementMatch(BaseModel):
    category: RequirementCategory
    requirement: str
    status: RequirementStatus
    evidence: str


class FitMatchAnalysis(BaseModel):
    matches: list[RequirementMatch]


class FitAssessment(BaseModel):
    score: int = Field(
        ge=0,
        le=100,
    )

    label: str
    recommendation: str

    component_scores: dict[str, int]
    component_weights: dict[str, int]

    matches: list[RequirementMatch]


# ============================================================
# PHASE 3 - APPLICATION GUIDANCE
# ============================================================


class ResumeSuggestion(BaseModel):
    change: str
    reason: str


class InterviewQuestion(BaseModel):
    question: str
    why_likely: str
    preparation_tip: str


class ApplicationAdvice(BaseModel):
    resume_adaptation: list[ResumeSuggestion]

    cover_letter_points: list[str]

    interview_questions: list[InterviewQuestion]

    skills_to_brush_up: list[str]
    company_research_topics: list[str]

    talking_points: list[str]
