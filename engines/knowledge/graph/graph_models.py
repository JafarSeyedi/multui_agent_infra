from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    metadata: dict | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
