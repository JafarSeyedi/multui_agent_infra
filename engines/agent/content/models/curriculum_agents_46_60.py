from ...models import AgentInput
from ...models import AgentOutput
from .common import ConfidenceScore
from .common import Evidence
from .common import Recommendation
from .learning_objects import ConceptNode
from .learning_objects import LearningObjective
from .learning_objects import Lesson
from .learning_objects import StudentProfile


# --------------------------------------------------
# Agent 46 — Concept Graph Builder
# --------------------------------------------------

class ConceptGraphBuilderInput(AgentInput):

    lessons: list[Lesson]


class ConceptGraphBuilderOutput(AgentOutput):

    concepts: list[ConceptNode]

    relationships: list[str]

    confidence: ConfidenceScore | None


# --------------------------------------------------
# Agent 47 — Concept Relation Extractor
# --------------------------------------------------

class ConceptRelationExtractorInput(AgentInput):

    concepts: list[ConceptNode]

    lesson_texts: list[str] | None


class ConceptRelationExtractorOutput(AgentOutput):

    extracted_relations: list[str]

    evidence: list[Evidence] | None


# --------------------------------------------------
# Agent 48 — Prerequisite Inference Agent
# --------------------------------------------------

class PrerequisiteInferenceInput(AgentInput):

    concepts: list[ConceptNode]


class PrerequisiteInferenceOutput(AgentOutput):

    prerequisite_pairs: list[str]

    confidence: ConfidenceScore | None


# --------------------------------------------------
# Agent 49 — Curriculum Planner
# --------------------------------------------------

class CurriculumPlannerInput(AgentInput):

    learning_objectives: list[LearningObjective]

    target_level: str | None


class CurriculumPlannerOutput(AgentOutput):

    curriculum_lessons: list[Lesson]

    rationale: str | None


# --------------------------------------------------
# Agent 50 — Lesson Sequence Planner
# --------------------------------------------------

class LessonSequencePlannerInput(AgentInput):

    lessons: list[Lesson]


class LessonSequencePlannerOutput(AgentOutput):

    ordered_lessons: list[Lesson]

    reasoning: str | None


# --------------------------------------------------
# Agent 51 — Learning Path Generator
# --------------------------------------------------

class LearningPathGeneratorInput(AgentInput):

    student: StudentProfile

    objectives: list[LearningObjective]


class LearningPathGeneratorOutput(AgentOutput):

    recommended_lessons: list[Lesson]

    recommendations: list[Recommendation] | None


# --------------------------------------------------
# Agent 52 — Personalized Curriculum Planner
# --------------------------------------------------

class PersonalizedCurriculumInput(AgentInput):

    student: StudentProfile

    curriculum_lessons: list[Lesson]


class PersonalizedCurriculumOutput(AgentOutput):

    personalized_lessons: list[Lesson]

    rationale: str | None


# --------------------------------------------------
# Agent 53 — Skill Gap Curriculum Adapter
# --------------------------------------------------

class SkillGapCurriculumAdapterInput(AgentInput):

    student: StudentProfile

    missing_concepts: list[str]


class SkillGapCurriculumAdapterOutput(AgentOutput):

    remedial_lessons: list[Lesson]

    recommendations: list[Recommendation] | None


# --------------------------------------------------
# Agent 54 — Difficulty Balancer
# --------------------------------------------------

class DifficultyBalancerInput(AgentInput):

    lessons: list[Lesson]

    student: StudentProfile


class DifficultyBalancerOutput(AgentOutput):

    balanced_lessons: list[Lesson]

    reasoning: str | None


# --------------------------------------------------
# Agent 55 — Study Strategy Planner
# --------------------------------------------------

class StudyStrategyPlannerInput(AgentInput):

    student: StudentProfile

    objectives: list[LearningObjective]


class StudyStrategyPlannerOutput(AgentOutput):

    study_plan: list[str]

    recommendations: list[Recommendation] | None


# --------------------------------------------------
# Agent 56 — Review Scheduler
# --------------------------------------------------

class ReviewSchedulerInput(AgentInput):

    concepts: list[ConceptNode]

    student: StudentProfile


class ReviewSchedulerOutput(AgentOutput):

    review_schedule: list[str]


# --------------------------------------------------
# Agent 57 — Remediation Planner
# --------------------------------------------------

class RemediationPlannerInput(AgentInput):

    student: StudentProfile

    weak_concepts: list[str]


class RemediationPlannerOutput(AgentOutput):

    remediation_lessons: list[Lesson]

    recommendations: list[Recommendation] | None


# --------------------------------------------------
# Agent 58 — Enrichment Planner
# --------------------------------------------------

class EnrichmentPlannerInput(AgentInput):

    student: StudentProfile

    mastered_concepts: list[str]


class EnrichmentPlannerOutput(AgentOutput):

    enrichment_lessons: list[Lesson]


# --------------------------------------------------
# Agent 59 — Concept Reinforcement Planner
# --------------------------------------------------

class ConceptReinforcementInput(AgentInput):

    concepts: list[ConceptNode]

    student: StudentProfile


class ConceptReinforcementOutput(AgentOutput):

    reinforcement_activities: list[str]


# --------------------------------------------------
# Agent 60 — Long-Term Learning Planner
# --------------------------------------------------

class LongTermLearningPlannerInput(AgentInput):

    student: StudentProfile

    long_term_goals: list[str]


class LongTermLearningPlannerOutput(AgentOutput):

    long_term_plan: list[str]

    milestones: list[str] | None
