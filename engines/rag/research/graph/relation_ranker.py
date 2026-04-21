from typing import List
from .relation_builder import CandidateRelation


class RelationRankingEngine:

    def __init__(self, min_confidence: float = 0.4):
        self.min_confidence = min_confidence

    def rank(self, relations: List[CandidateRelation]) -> List[CandidateRelation]:

        scored = []

        for r in relations:

            score = r.confidence

            # relation weighting
            if r.relation in ["extends", "based_on"]:
                score += 0.2

            if r.relation == "co_occurs":
                score -= 0.2

            if score >= self.min_confidence:
                r.confidence = score
                scored.append(r)

        scored.sort(key=lambda x: x.confidence, reverse=True)

        return scored
