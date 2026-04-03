from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .schema import (
    FailureEvent,
    FailureResponse,
    GraphPath,
    GraphPathsResponse,
    MemoryUsageResponse,
    RetrievalChunkStat,
    RetrievalHeatmapResponse,
    TokenBreakdownResponse,
    TokenUsage,
)
from .websocket_stream import WebSocketStream


def create_dashboard(observability) -> FastAPI:
    app = FastAPI(title="Research Engine Observability", version="1.0")
    stream = WebSocketStream(observability)

    @app.get("/tokens", response_model=TokenBreakdownResponse)
    def token_usage():
        breakdown = observability.token_tracker.breakdown()
        modules = [TokenUsage(module=module, tokens=tokens) for module, tokens in breakdown.items()]
        return TokenBreakdownResponse(total_tokens=observability.token_tracker.total(), modules=modules)

    @app.get("/retrieval_heatmap", response_model=RetrievalHeatmapResponse)
    def retrieval_heatmap():
        chunks = [RetrievalChunkStat(chunk_id=chunk_id, hits=hits) for chunk_id, hits in observability.retrieval_heatmap.top_chunks()]
        return RetrievalHeatmapResponse(chunks=chunks)

    @app.get("/graph_paths", response_model=GraphPathsResponse)
    def graph_paths():
        paths = [GraphPath(nodes=path) for path in observability.graph_visualizer.get_paths()]
        return GraphPathsResponse(paths=paths)

    @app.get("/memory", response_model=MemoryUsageResponse)
    def memory():
        return MemoryUsageResponse(rss_bytes=observability.memory_tracker.current())

    @app.get("/failures", response_model=FailureResponse)
    def failures():
        items = [FailureEvent(module=item["module"], error=item["error"]) for item in observability.failure_analyzer.recent()]
        return FailureResponse(failures=items)

    @app.websocket("/live")
    async def live_stream(websocket: WebSocket):
        await stream.connect(websocket)
        try:
            await stream.stream_client(websocket)
        except WebSocketDisconnect:
            pass
        finally:
            stream.disconnect(websocket)

    return app
