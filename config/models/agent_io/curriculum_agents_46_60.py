from typing import List, Optional
from agents.orchestration.models import OrchestrationRequest, OrchestrationResult

from .common import ConfidenceScore, Recommendation, Evidence
from .learning_objects import (
    ConceptNode,
    Lesson,
    LearningObjective,
    StudentProfile
)


# --------------------------------------------------
# Agent 46 — Concept Graph Builder
# --------------------------------------------------

class ConceptGraphBuilderInput(OrchestrationRequest):

    lessons: List[Lesson]


class ConceptGraphBuilderOutput(OrchestrationResult):

    concepts: List[ConceptNode]

    relationships: List[str]

    confidence: Optional[ConfidenceScore]


# --------------------------------------------------
# Agent 47 — Concept Relation Extractor
# --------------------------------------------------

class ConceptRelationExtractorInput(OrchestrationRequest):

    concepts: List[ConceptNode]

    lesson_texts: Optional[List[str]]


class ConceptRelationExtractorOutput(OrchestrationResult):

    extracted_relations: List[str]

    evidence: Optional[List[Evidence]]


# --------------------------------------------------
# Agent 48 — Prerequisite Inference Agent
# --------------------------------------------------

class PrerequisiteInferenceInput(OrchestrationRequest):

    concepts: List[ConceptNode]


class PrerequisiteInferenceOutput(OrchestrationResult):

    prerequisite_pairs: List[str]

    confidence: Optional[ConfidenceScore]


# --------------------------------------------------
# Agent 49 — Curriculum Planner
# --------------------------------------------------

class CurriculumPlannerInput(OrchestrationRequest):

    learning_objectives: List[LearningObjective]

    target_level: Optional[str]


class CurriculumPlannerOutput(OrchestrationResult):

    curriculum_lessons: List[Lesson]

    rationale: Optional[str]


# --------------------------------------------------
# Agent 50 — Lesson Sequence Planner
# --------------------------------------------------

class LessonSequencePlannerInput(OrchestrationRequest):

    lessons: List[Lesson]


class LessonSequencePlannerOutput(OrchestrationResult):

    ordered_lessons: List[Lesson]

    reasoning: Optional[str]


# --------------------------------------------------
# Agent 51 — Learning Path Generator
# --------------------------------------------------

class LearningPathGeneratorInput(OrchestrationRequest):

    student: StudentProfile

    objectives: List[LearningObjective]


class LearningPathGeneratorOutput(OrchestrationResult):

    recommended_lessons: List[Lesson]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 52 — Personalized Curriculum Planner
# --------------------------------------------------

class PersonalizedCurriculumInput(OrchestrationRequest):

    student: StudentProfile

    curriculum_lessons: List[Lesson]


class PersonalizedCurriculumOutput(OrchestrationResult):

    personalized_lessons: List[Lesson]

    rationale: Optional[str]


# --------------------------------------------------
# Agent 53 — Skill Gap Curriculum Adapter
# --------------------------------------------------

class SkillGapCurriculumAdapterInput(OrchestrationRequest):

    student: StudentProfile

    missing_concepts: List[str]


class SkillGapCurriculumAdapterOutput(OrchestrationResult):

    remedial_lessons: List[Lesson]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 54 — Difficulty Balancer
# --------------------------------------------------

class DifficultyBalancerInput(OrchestrationRequest):

    lessons: List[Lesson]

    student: StudentProfile


class DifficultyBalancerOutput(OrchestrationResult):

    balanced_lessons: List[Lesson]

    reasoning: Optional[str]


# --------------------------------------------------
# Agent 55 — Study Strategy Planner
# --------------------------------------------------

class StudyStrategyPlannerInput(OrchestrationRequest):

    student: StudentProfile

    objectives: List[LearningObjective]


class StudyStrategyPlannerOutput(OrchestrationResult):

    study_plan: List[str]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 56 — Review Scheduler
# --------------------------------------------------

class ReviewSchedulerInput(OrchestrationRequest):

    concepts: List[ConceptNode]

    student: StudentProfile


class ReviewSchedulerOutput(OrchestrationResult):

    review_schedule: List[str]


# --------------------------------------------------
# Agent 57 — Remediation Planner
# --------------------------------------------------

class RemediationPlannerInput(OrchestrationRequest):

    student: StudentProfile

    weak_concepts: List[str]


class RemediationPlannerOutput(OrchestrationResult):

    remediation_lessons: List[Lesson]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 58 — Enrichment Planner
# --------------------------------------------------

class EnrichmentPlannerInput(OrchestrationRequest):

    student: StudentProfile

    mastered_concepts: List[str]


class EnrichmentPlannerOutput(OrchestrationResult):

    enrichment_lessons: List[Lesson]


# --------------------------------------------------
# Agent 59 — Concept Reinforcement Planner
# --------------------------------------------------

class ConceptReinforcementInput(OrchestrationRequest):

    concepts: List[ConceptNode]

    student: StudentProfile


class ConceptReinforcementOutput(OrchestrationResult):

    reinforcement_activities: List[str]


# --------------------------------------------------
# Agent 60 — Long-Term Learning Planner
# --------------------------------------------------

class LongTermLearningPlannerInput(OrchestrationRequest):

    student: StudentProfile

    long_term_goals: List[str]


class LongTermLearningPlannerOutput(OrchestrationResult):

    long_term_plan: List[str]

    milestones: Optional[List[str]]
