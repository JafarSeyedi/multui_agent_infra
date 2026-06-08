from datetime import datetime

from pydantic import BaseModel

from ...models import AgentInput
from ...models import AgentOutput


# Agent1: Text Rewriter (Text Rewriter)
## Input
class TextRewriteInput(AgentInput):

    raw_text: str

    grade_level: str

    glossary: dict[str,str] | None = None

    subject: str | None = None

    language: str = "fa"

## Output
class RewriteChange(BaseModel):

    original_segment: str
    rewritten_segment: str
    reason: str | None = None


class TextRewriteOutput(AgentOutput):

    rewritten_text: str

    changes: list[RewriteChange]

    readability_score: float | None

    created_at: datetime


# Agent2 Content Validator
## Input
class ContentValidationInput(AgentInput):

    content_text: str

    trusted_sources: list[str]

    subject: str | None

    grade_level: str | None

## Output
class ValidationIssue(BaseModel):

    sentence: str
    issue_type: str
    explanation: str
    suggested_fix: str | None


class ContentValidationOutput(AgentOutput):

    verified_statements: list[str]

    suspicious_statements: list[ValidationIssue]

    correction_suggestions: list[str]

    overall_trust_score: float


# Agent 3  ارجاع‌ساز (Citation Generator)
## Input
class CitationGenerationInput(AgentInput):

    content_text: str

    citation_style: str

    preferred_sources: list[str] | None

## Output
class CitationEntry(BaseModel):

    reference_id: str
    source_title: str
    authors: list[str]
    year: int | None
    link: str | None

class CitationGenerationOutput(AgentOutput):

    cited_text: str

    references: list[CitationEntry]


# Agent 4  واژه‌نامه‌ساز (Glossary Builder)
## Input
class GlossaryBuilderInput(AgentInput):

    lesson_text: str

    terminology_database: list[str] | None

    subject: str | None

    grade_level: str | None

## Output
class GlossaryTerm(BaseModel):

    term: str

    definition: str

    examples: list[str]

    related_links: list[str] | None


class GlossaryBuilderOutput(AgentOutput):

    glossary_terms: list[GlossaryTerm]


# Agent 5 به‌روزرسانی پویا (Dynamic Content Update)
## Input
class DynamicUpdateInput(AgentInput):

    current_content: str

    new_sources: list[str]

    subject: str | None

## Output
class ContentUpdateSuggestion(BaseModel):

    section: str
    current_text: str
    suggested_update: str
    reason: str


class DynamicUpdateOutput(AgentOutput):

    updates: list[ContentUpdateSuggestion]

    change_summary: str


# Agent 6 روایت‌ساز (Narrative Builder)
## Input

class NarrativeBuilderInput(AgentInput):

    lesson_content: str

    student_age: int

    student_interests: list[str] | None

    subject: str | None

## Output
class NarrativeElement(BaseModel):

    type: str   # dialogue, explanation, story, image_prompt

    content: str


class NarrativeBuilderOutput(AgentOutput):

    narrative_lesson: list[NarrativeElement]

    narrative_style: str


# Agent 7  ساختاردهی خودکار (Auto Structurer)
## Input
class StructuringInput(AgentInput):

    raw_text: str

    learning_objectives: list[str]

    subject: str | None


## Output
class LessonSection(BaseModel):

    title: str

    content: str

    subsections: list[str] | None


class StructuringOutput(AgentOutput):

    structured_sections: list[LessonSection]

    table_of_contents: list[str]


# Agent 8  پیشینه‌ساز (Prerequisite Builder)
## Input
class PrerequisiteInput(AgentInput):

    topic: str

    student_weaknesses: list[str] | None

    subject: str | None

## Output
class PrerequisiteItem(BaseModel):

    concept: str

    explanation: str

    review_resource_link: str | None


class PrerequisiteOutput(AgentOutput):

    prerequisites: list[PrerequisiteItem]


# Agent
## Input
## Output
