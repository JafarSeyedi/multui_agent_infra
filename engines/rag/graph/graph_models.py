from pydantic import BaseModel
from typing import Optional


class GraphNode(BaseModel):

    id: str
    label: str
    type: str
    metadata: Optional[dict] = None


class GraphEdge(BaseModel):

    source: str
    target: str
    relation: str
