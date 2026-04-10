# rag/rag_models.py
from pydantic import BaseModel
from typing import List, Optional, Dict


class Document(BaseModel):
    document_id: str
    title: Optional[str] = None
    source: Optional[str] = None
    metadata: Optional[Dict] = None


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict] = None


class RetrievedDocument(BaseModel):
    chunk: DocumentChunk
    score: float
    document: Optional[Document] = None
