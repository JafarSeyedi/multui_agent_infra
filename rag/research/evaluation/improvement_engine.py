class ImprovementEngine:

    def suggest(self, evaluation):

        suggestions = []

        if evaluation.retrieval_quality < 0.6:

            suggestions.append(
                "Improve retriever: increase top_k or refine embeddings"
            )

        if evaluation.hallucination_rate > 0.3:

            suggestions.append(
                "Reduce hallucination: enforce citation grounding"
            )

        if evaluation.completeness_score < 0.6:

            suggestions.append(
                "Increase research depth and follow-up queries"
            )

        if evaluation.reasoning_score < 0.6:

            suggestions.append(
                "Enable graph reasoning traversal"
            )

        return suggestions
