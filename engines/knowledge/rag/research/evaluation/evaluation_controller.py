from .citation_evaluator import CitationEvaluator
from .completeness_evaluator import CompletenessEvaluator
from .coverage_scorer import CoverageScorer
from .hallucination_detector import HallucinationDetector
from .reasoning_evaluator import ReasoningEvaluator
from .retrieval_evaluator import RetrievalEvaluator
from .schema import EvaluationResult


class EvaluationController:

    def __init__(self, llm):

        self.retrieval = RetrievalEvaluator(llm)
        self.citation = CitationEvaluator(llm)
        self.hallucination = HallucinationDetector(llm)
        self.reasoning = ReasoningEvaluator(llm)
        self.completeness = CompletenessEvaluator(llm)
        self.coverage = CoverageScorer()

    def evaluate(self, research_answer):

        retrieval_quality = self.retrieval.evaluate(
            research_answer.query,
            research_answer.evidences
        )

        citation_accuracy = self.citation.evaluate(
            research_answer.answer,
            research_answer.evidences
        )

        hallucination_rate = self.hallucination.detect(
            research_answer.answer,
            research_answer.evidences
        )

        reasoning_score = self.reasoning.evaluate(
            research_answer.reasoning_steps
        )

        completeness_score = self.completeness.evaluate(
            research_answer.query,
            research_answer.answer
        )

        coverage_score = self.coverage.score(
            research_answer.evidences
        )

        return EvaluationResult(
            retrieval_quality=retrieval_quality,
            citation_accuracy=citation_accuracy,
            hallucination_rate=hallucination_rate,
            reasoning_score=reasoning_score,
            completeness_score=completeness_score,
            coverage_score=coverage_score
        )
