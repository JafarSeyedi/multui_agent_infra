from __future__ import annotations


class MetricsStore:
    def __init__(self, observability=None):
        self.observability = observability

    def snapshot(self):
        if self.observability is None:
            return {}
        return {
            "total_tokens": self.observability.token_tracker.total(),
            "token_breakdown": self.observability.token_tracker.breakdown(),
            "top_retrieval_chunks": self.observability.retrieval_heatmap.top_chunks(),
            "graph_paths": self.observability.graph_visualizer.get_paths(),
            "memory_rss": self.observability.memory_tracker.current(),
            "recent_failures": self.observability.failure_analyzer.recent(),
        }
