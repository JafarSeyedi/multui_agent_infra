from pydantic import BaseModel
from agents.base_agents.models import AgentInput, AgentOutput
from typing import List, Optional, Dict
from datetime import datetime


# Agent1: بازنویس متون (Text Rewriter)
## Input
class TextRewriteInput(AgentInput):

    raw_text: str

    grade_level: str

    glossary: Optional[Dict[str,str]] = None

    subject: Optional[str] = None

    language: str = "fa"

## Output
class RewriteChange(BaseModel):

    original_segment: str
    rewritten_segment: str
    reason: Optional[str] = None


class TextRewriteOutput(AgentOutput):

    rewritten_text: str

    changes: List[RewriteChange]

    readability_score: Optional[float]

    created_at: datetime


# Agent2 اعتبارسنج محتوا (Content Validator)
## Input
class ContentValidationInput(AgentInput):

    content_text: str

    trusted_sources: List[str]

    subject: Optional[str]

    grade_level: Optional[str]

## Output
class ValidationIssue(BaseModel):

    sentence: str
    issue_type: str
    explanation: str
    suggested_fix: Optional[str]


class ContentValidationOutput(AgentOutput):

    verified_statements: List[str]

    suspicious_statements: List[ValidationIssue]

    correction_suggestions: List[str]

    overall_trust_score: float


# Agent 3  ارجاع‌ساز (Citation Generator)
## Input
class CitationGenerationInput(AgentInput):

    content_text: str

    citation_style: str

    preferred_sources: Optional[List[str]]

## Output
class CitationEntry(BaseModel):

    reference_id: str
    source_title: str
    authors: List[str]
    year: Optional[int]
    link: Optional[str]

class CitationGenerationOutput(AgentOutput):

    cited_text: str

    references: List[CitationEntry]


# Agent 4  واژه‌نامه‌ساز (Glossary Builder)
## Input
class GlossaryBuilderInput(AgentInput):

    lesson_text: str

    terminology_database: Optional[List[str]]

    subject: Optional[str]

    grade_level: Optional[str]

## Output
class GlossaryTerm(BaseModel):

    term: str

    definition: str

    examples: List[str]

    related_links: Optional[List[str]]


class GlossaryBuilderOutput(AgentOutput):

    glossary_terms: List[GlossaryTerm]


# Agent 5 به‌روزرسانی پویا (Dynamic Content Update)
## Input
class DynamicUpdateInput(AgentInput):

    current_content: str

    new_sources: List[str]

    subject: Optional[str]

## Output
class ContentUpdateSuggestion(BaseModel):

    section: str
    current_text: str
    suggested_update: str
    reason: str


class DynamicUpdateOutput(AgentOutput):

    updates: List[ContentUpdateSuggestion]

    change_summary: str


# Agent 6 روایت‌ساز (Narrative Builder)
## Input

class NarrativeBuilderInput(AgentInput):

    lesson_content: str

    student_age: int

    student_interests: Optional[List[str]]

    subject: Optional[str]

## Output
class NarrativeElement(BaseModel):

    type: str   # dialogue, explanation, story, image_prompt

    content: str


class NarrativeBuilderOutput(AgentOutput):

    narrative_lesson: List[NarrativeElement]

    narrative_style: str


# Agent 7  ساختاردهی خودکار (Auto Structurer)
## Input
class StructuringInput(AgentInput):

    raw_text: str

    learning_objectives: List[str]

    subject: Optional[str]


## Output
class LessonSection(BaseModel):

    title: str

    content: str

    subsections: Optional[List[str]]


class StructuringOutput(AgentOutput):

    structured_sections: List[LessonSection]

    table_of_contents: List[str]


# Agent 8  پیشینه‌ساز (Prerequisite Builder)
## Input
class PrerequisiteInput(AgentInput):

    topic: str

    student_weaknesses: Optional[List[str]]

    subject: Optional[str]

## Output
class PrerequisiteItem(BaseModel):

    concept: str

    explanation: str

    review_resource_link: Optional[str]


class PrerequisiteOutput(AgentOutput):

    prerequisites: List[PrerequisiteItem]


# Agent 
## Input
## Output
