# rag/rag_models.py
from pydantic import BaseModel


class Document(BaseModel):
    document_id: str
    title: str | None = None
    source: str | None = None
    metadata: dict | None = None


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    embedding: list[float] | None = None
    metadata: dict | None = None


class RetrievedDocument(BaseModel):
    chunk: DocumentChunk
    score: float
    document: Document | None = None
