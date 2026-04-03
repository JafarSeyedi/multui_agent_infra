from pydantic import BaseModel
from typing import List, Optional

from .common import ConfidenceScore, Recommendation, Evidence
from config.models.core.learning_objects import (
    ConceptNode,
    Lesson,
    LearningObjective,
    StudentProfile
)


# --------------------------------------------------
# Agent 46 — Concept Graph Builder
# --------------------------------------------------

class ConceptGraphBuilderInput(BaseModel):

    lessons: List[Lesson]


class ConceptGraphBuilderOutput(BaseModel):

    concepts: List[ConceptNode]

    relationships: List[str]

    confidence: Optional[ConfidenceScore]


# --------------------------------------------------
# Agent 47 — Concept Relation Extractor
# --------------------------------------------------

class ConceptRelationExtractorInput(BaseModel):

    concepts: List[ConceptNode]

    lesson_texts: Optional[List[str]]


class ConceptRelationExtractorOutput(BaseModel):

    extracted_relations: List[str]

    evidence: Optional[List[Evidence]]


# --------------------------------------------------
# Agent 48 — Prerequisite Inference Agent
# --------------------------------------------------

class PrerequisiteInferenceInput(BaseModel):

    concepts: List[ConceptNode]


class PrerequisiteInferenceOutput(BaseModel):

    prerequisite_pairs: List[str]

    confidence: Optional[ConfidenceScore]


# --------------------------------------------------
# Agent 49 — Curriculum Planner
# --------------------------------------------------

class CurriculumPlannerInput(BaseModel):

    learning_objectives: List[LearningObjective]

    target_level: Optional[str]


class CurriculumPlannerOutput(BaseModel):

    curriculum_lessons: List[Lesson]

    rationale: Optional[str]


# --------------------------------------------------
# Agent 50 — Lesson Sequence Planner
# --------------------------------------------------

class LessonSequencePlannerInput(BaseModel):

    lessons: List[Lesson]


class LessonSequencePlannerOutput(BaseModel):

    ordered_lessons: List[Lesson]

    reasoning: Optional[str]


# --------------------------------------------------
# Agent 51 — Learning Path Generator
# --------------------------------------------------

class LearningPathGeneratorInput(BaseModel):

    student: StudentProfile

    objectives: List[LearningObjective]


class LearningPathGeneratorOutput(BaseModel):

    recommended_lessons: List[Lesson]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 52 — Personalized Curriculum Planner
# --------------------------------------------------

class PersonalizedCurriculumInput(BaseModel):

    student: StudentProfile

    curriculum_lessons: List[Lesson]


class PersonalizedCurriculumOutput(BaseModel):

    personalized_lessons: List[Lesson]

    rationale: Optional[str]


# --------------------------------------------------
# Agent 53 — Skill Gap Curriculum Adapter
# --------------------------------------------------

class SkillGapCurriculumAdapterInput(BaseModel):

    student: StudentProfile

    missing_concepts: List[str]


class SkillGapCurriculumAdapterOutput(BaseModel):

    remedial_lessons: List[Lesson]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 54 — Difficulty Balancer
# --------------------------------------------------

class DifficultyBalancerInput(BaseModel):

    lessons: List[Lesson]

    student: StudentProfile


class DifficultyBalancerOutput(BaseModel):

    balanced_lessons: List[Lesson]

    reasoning: Optional[str]


# --------------------------------------------------
# Agent 55 — Study Strategy Planner
# --------------------------------------------------

class StudyStrategyPlannerInput(BaseModel):

    student: StudentProfile

    objectives: List[LearningObjective]


class StudyStrategyPlannerOutput(BaseModel):

    study_plan: List[str]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 56 — Review Scheduler
# --------------------------------------------------

class ReviewSchedulerInput(BaseModel):

    concepts: List[ConceptNode]

    student: StudentProfile


class ReviewSchedulerOutput(BaseModel):

    review_schedule: List[str]


# --------------------------------------------------
# Agent 57 — Remediation Planner
# --------------------------------------------------

class RemediationPlannerInput(BaseModel):

    student: StudentProfile

    weak_concepts: List[str]


class RemediationPlannerOutput(BaseModel):

    remediation_lessons: List[Lesson]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 58 — Enrichment Planner
# --------------------------------------------------

class EnrichmentPlannerInput(BaseModel):

    student: StudentProfile

    mastered_concepts: List[str]


class EnrichmentPlannerOutput(BaseModel):

    enrichment_lessons: List[Lesson]


# --------------------------------------------------
# Agent 59 — Concept Reinforcement Planner
# --------------------------------------------------

class ConceptReinforcementInput(BaseModel):

    concepts: List[ConceptNode]

    student: StudentProfile


class ConceptReinforcementOutput(BaseModel):

    reinforcement_activities: List[str]


# --------------------------------------------------
# Agent 60 — Long-Term Learning Planner
# --------------------------------------------------

class LongTermLearningPlannerInput(BaseModel):

    student: StudentProfile

    long_term_goals: List[str]


class LongTermLearningPlannerOutput(BaseModel):

    long_term_plan: List[str]

    milestones: Optional[List[str]]
