from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PEER_REVIEWED_JOURNAL = "peer_reviewed_journal"
    NEWS_ORGANIZATION = "news_organization"
    GOVERNMENT_AGENCY = "government_agency"
    NONPROFIT_ORGANIZATION = "nonprofit_organization"
    CORPORATE_BLOG = "corporate_blog"
    PERSONAL_BLOG = "personal_blog"
    SOCIAL_MEDIA = "social_media"
    WIKI = "wiki"
    UNKNOWN = "unknown"


class EditorialProcess(str, Enum):
    PEER_REVIEWED = "peer_reviewed"
    EDITOR_REVIEWED = "editor_reviewed"
    SELF_PUBLISHED = "self_published"
    UNKNOWN = "unknown"


class SourceLevel(str, Enum):
    PRIMARY_SOURCE = "primary_source"
    SECONDARY_SOURCE = "secondary_source"
    TERTIARY_SOURCE = "tertiary_source"


class CredibilityRating(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class AuthorInfo(BaseModel):
    name: str = Field(
        description=(
            'Author name. Use "Unknown" if the author cannot be identified '
            "after investigation."
        )
    )

    credentials: str = Field(
        description=(
            "Known qualifications, expertise, affiliations, and background. "
            "If unavailable, explain what was searched."
        )
    )

    credibility_assessment: str = Field(
        description=(
            "Assessment of the author's credibility and how any missing "
            "information affects the source evaluation."
        )
    )


class PublicationInfo(BaseModel):
    name: str = Field(
        description=(
            "Name of the publication or website. Use the domain name if the "
            "publication does not have a recognized name."
        )
    )

    reputation: str = Field(
        description=(
            "What the investigation found about the publication's reputation, "
            "ownership, reliability, and editorial standards. If unknown, "
            "explain what was searched."
        )
    )

    editorial_process: EditorialProcess = Field(
        description=(
            "The type of review process used by the publication: peer reviewed, "
            "editor reviewed, self published, or unknown."
        )
    )


class ContentAnalysis(BaseModel):
    claims_supported_by_evidence: bool = Field(
        description=(
            "Whether the main claims are supported by data, citations, "
            "research, or other verifiable evidence."
        )
    )

    sources_cited: bool = Field(
        description=(
            "Whether the source clearly cites references, research, "
            "documents, or primary sources."
        )
    )

    corroborated_by_other_sources: bool = Field(
        description=(
            "Whether other credible and independent sources support "
            "the main claims."
        )
    )

    contradicted_by_other_sources: bool = Field(
        description=(
            "Whether credible sources were found that contradict "
            "the main claims."
        )
    )

    primary_vs_secondary: SourceLevel = Field(
        description=(
            "Classify the source as a primary, secondary, or tertiary source."
        )
    )

    funding_or_sponsorship: str = Field(
        description=(
            "Known funding, ownership, advertising, sponsorship, or possible "
            "financial conflicts. Explain if this could not be determined."
        )
    )

    date_published: str = Field(
        description=(
            "The publication date and whether the information is still current. "
            'Use "Unknown" if no date can be found.'
        )
    )

    bias_and_tone: str = Field(
        description=(
            "Describe whether the language is neutral, emotional, persuasive, "
            "one-sided, or balanced, and whether counterarguments are included."
        )
    )


class CredibilityEvaluation(BaseModel):
    source_url: str = Field(
        description="The complete URL of the source being evaluated."
    )

    source_type: SourceType = Field(
        description="The category that best describes the source."
    )

    author: AuthorInfo = Field(
        description="Information discovered about the source's author."
    )

    publication: PublicationInfo = Field(
        description="Information discovered about the publication or website."
    )

    content_analysis: ContentAnalysis = Field(
        description=(
            "Evidence, citations, corroboration, contradictions, funding, "
            "currency, and bias analysis."
        )
    )

    transparency_score: int = Field(
        ge=1,
        le=5,
        description=(
            "Transparency rating from 1 to 5 based on whether the source clearly "
            "identifies its author, methods, evidence, ownership, and funding."
        ),
    )

    overall_credibility: CredibilityRating = Field(
        description="Final credibility rating: high, medium, low, or very low."
    )

    reasoning: str = Field(
        description=(
            "Detailed explanation of the final rating using specific evidence "
            "found during the investigation. Clearly identify any information "
            "that could not be verified."
        )
    )