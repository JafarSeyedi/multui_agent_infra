from typing import List, Optional
from engines.agents.models import AgentInput, AgentOutput

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

class ConceptGraphBuilderInput(AgentInput):

    lessons: List[Lesson]


class ConceptGraphBuilderOutput(AgentOutput):

    concepts: List[ConceptNode]

    relationships: List[str]

    confidence: Optional[ConfidenceScore]


# --------------------------------------------------
# Agent 47 — Concept Relation Extractor
# --------------------------------------------------

class ConceptRelationExtractorInput(AgentInput):

    concepts: List[ConceptNode]

    lesson_texts: Optional[List[str]]


class ConceptRelationExtractorOutput(AgentOutput):

    extracted_relations: List[str]

    evidence: Optional[List[Evidence]]


# --------------------------------------------------
# Agent 48 — Prerequisite Inference Agent
# --------------------------------------------------

class PrerequisiteInferenceInput(AgentInput):

    concepts: List[ConceptNode]


class PrerequisiteInferenceOutput(AgentOutput):

    prerequisite_pairs: List[str]

    confidence: Optional[ConfidenceScore]


# --------------------------------------------------
# Agent 49 — Curriculum Planner
# --------------------------------------------------

class CurriculumPlannerInput(AgentInput):

    learning_objectives: List[LearningObjective]

    target_level: Optional[str]


class CurriculumPlannerOutput(AgentOutput):

    curriculum_lessons: List[Lesson]

    rationale: Optional[str]


# --------------------------------------------------
# Agent 50 — Lesson Sequence Planner
# --------------------------------------------------

class LessonSequencePlannerInput(AgentInput):

    lessons: List[Lesson]


class LessonSequencePlannerOutput(AgentOutput):

    ordered_lessons: List[Lesson]

    reasoning: Optional[str]


# --------------------------------------------------
# Agent 51 — Learning Path Generator
# --------------------------------------------------

class LearningPathGeneratorInput(AgentInput):

    student: StudentProfile

    objectives: List[LearningObjective]


class LearningPathGeneratorOutput(AgentOutput):

    recommended_lessons: List[Lesson]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 52 — Personalized Curriculum Planner
# --------------------------------------------------

class PersonalizedCurriculumInput(AgentInput):

    student: StudentProfile

    curriculum_lessons: List[Lesson]


class PersonalizedCurriculumOutput(AgentOutput):

    personalized_lessons: List[Lesson]

    rationale: Optional[str]


# --------------------------------------------------
# Agent 53 — Skill Gap Curriculum Adapter
# --------------------------------------------------

class SkillGapCurriculumAdapterInput(AgentInput):

    student: StudentProfile

    missing_concepts: List[str]


class SkillGapCurriculumAdapterOutput(AgentOutput):

    remedial_lessons: List[Lesson]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 54 — Difficulty Balancer
# --------------------------------------------------

class DifficultyBalancerInput(AgentInput):

    lessons: List[Lesson]

    student: StudentProfile


class DifficultyBalancerOutput(AgentOutput):

    balanced_lessons: List[Lesson]

    reasoning: Optional[str]


# --------------------------------------------------
# Agent 55 — Study Strategy Planner
# --------------------------------------------------

class StudyStrategyPlannerInput(AgentInput):

    student: StudentProfile

    objectives: List[LearningObjective]


class StudyStrategyPlannerOutput(AgentOutput):

    study_plan: List[str]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 56 — Review Scheduler
# --------------------------------------------------

class ReviewSchedulerInput(AgentInput):

    concepts: List[ConceptNode]

    student: StudentProfile


class ReviewSchedulerOutput(AgentOutput):

    review_schedule: List[str]


# --------------------------------------------------
# Agent 57 — Remediation Planner
# --------------------------------------------------

class RemediationPlannerInput(AgentInput):

    student: StudentProfile

    weak_concepts: List[str]


class RemediationPlannerOutput(AgentOutput):

    remediation_lessons: List[Lesson]

    recommendations: Optional[List[Recommendation]]


# --------------------------------------------------
# Agent 58 — Enrichment Planner
# --------------------------------------------------

class EnrichmentPlannerInput(AgentInput):

    student: StudentProfile

    mastered_concepts: List[str]


class EnrichmentPlannerOutput(AgentOutput):

    enrichment_lessons: List[Lesson]


# --------------------------------------------------
# Agent 59 — Concept Reinforcement Planner
# --------------------------------------------------

class ConceptReinforcementInput(AgentInput):

    concepts: List[ConceptNode]

    student: StudentProfile


class ConceptReinforcementOutput(AgentOutput):

    reinforcement_activities: List[str]


# --------------------------------------------------
# Agent 60 — Long-Term Learning Planner
# --------------------------------------------------

class LongTermLearningPlannerInput(AgentInput):

    student: StudentProfile

    long_term_goals: List[str]


class LongTermLearningPlannerOutput(AgentOutput):

    long_term_plan: List[str]

    milestones: Optional[List[str]]
