from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


# Agent1: بازنویس متون (Text Rewriter)
## Input
class TextRewriteInput(BaseModel):

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


class TextRewriteOutput(BaseModel):

    rewritten_text: str

    changes: List[RewriteChange]

    readability_score: Optional[float]

    created_at: datetime


# Agent2 اعتبارسنج محتوا (Content Validator)
## Input
class ContentValidationInput(BaseModel):

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


class ContentValidationOutput(BaseModel):

    verified_statements: List[str]

    suspicious_statements: List[ValidationIssue]

    correction_suggestions: List[str]

    overall_trust_score: float


# Agent 3  ارجاع‌ساز (Citation Generator)
## Input
class CitationGenerationInput(BaseModel):

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

class CitationGenerationOutput(BaseModel):

    cited_text: str

    references: List[CitationEntry]


# Agent 4  واژه‌نامه‌ساز (Glossary Builder)
## Input
class GlossaryBuilderInput(BaseModel):

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


class GlossaryBuilderOutput(BaseModel):

    glossary_terms: List[GlossaryTerm]


# Agent 5 به‌روزرسانی پویا (Dynamic Content Update)
## Input
class DynamicUpdateInput(BaseModel):

    current_content: str

    new_sources: List[str]

    subject: Optional[str]

## Output
class ContentUpdateSuggestion(BaseModel):

    section: str
    current_text: str
    suggested_update: str
    reason: str


class DynamicUpdateOutput(BaseModel):

    updates: List[ContentUpdateSuggestion]

    change_summary: str


# Agent 6 روایت‌ساز (Narrative Builder)
## Input

class NarrativeBuilderInput(BaseModel):

    lesson_content: str

    student_age: int

    student_interests: Optional[List[str]]

    subject: Optional[str]

## Output
class NarrativeElement(BaseModel):

    type: str   # dialogue, explanation, story, image_prompt

    content: str


class NarrativeBuilderOutput(BaseModel):

    narrative_lesson: List[NarrativeElement]

    narrative_style: str


# Agent 7  ساختاردهی خودکار (Auto Structurer)
## Input
class StructuringInput(BaseModel):

    raw_text: str

    learning_objectives: List[str]

    subject: Optional[str]


## Output
class LessonSection(BaseModel):

    title: str

    content: str

    subsections: Optional[List[str]]


class StructuringOutput(BaseModel):

    structured_sections: List[LessonSection]

    table_of_contents: List[str]


# Agent 8  پیشینه‌ساز (Prerequisite Builder)
## Input
class PrerequisiteInput(BaseModel):

    topic: str

    student_weaknesses: Optional[List[str]]

    subject: Optional[str]

## Output
class PrerequisiteItem(BaseModel):

    concept: str

    explanation: str

    review_resource_link: Optional[str]


class PrerequisiteOutput(BaseModel):

    prerequisites: List[PrerequisiteItem]


# Agent 
## Input
## Output
