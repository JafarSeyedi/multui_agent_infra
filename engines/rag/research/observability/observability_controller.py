from __future__ import annotations

from .failure_analyzer import FailureAnalyzer
from .graph_visualizer import GraphVisualizer
from .memory_usage_tracker import MemoryUsageTracker
from .retrieval_heatmap import RetrievalHeatmap
from .telemetry import Telemetry
from .token_tracker import TokenTracker
from .trace_collector import TraceCollector


class ObservabilityController:
    def __init__(self):
        self.collector = TraceCollector()
        self.telemetry = Telemetry(self.collector)
        self.retrieval_heatmap = RetrievalHeatmap()
        self.token_tracker = TokenTracker()
        self.graph_visualizer = GraphVisualizer()
        self.memory_tracker = MemoryUsageTracker()
        self.failure_analyzer = FailureAnalyzer()

    def track_research_session(self, query: str, duration: float, evidence_count: int) -> None:
        self.telemetry.emit(
            "research_session",
            {
                "query": query,
                "duration": duration,
                "evidence_count": evidence_count,
                "memory_rss": self.memory_tracker.current(),
            },
        )
