from typing import List, Dict
from config.models.rag.rag_models import Document, DocumentChunk


class DocumentStore:
    """Manages documents and their chunks."""

    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.chunks: Dict[str, DocumentChunk] = {}

    def add_document(self, doc: Document):
        self.documents[doc.document_id] = doc

    def add_chunks(self, chunks: List[DocumentChunk]):
        for ch in chunks:
            self.chunks[ch.chunk_id] = ch

    def get_chunks_by_doc(self, document_id: str) -> List[DocumentChunk]:
        return [c for c in self.chunks.values() if c.document_id == document_id]

    def search_by_keyword(self, keyword: str) -> List[DocumentChunk]:
        return [
            c for c in self.chunks.values()
            if keyword.lower() in c.text.lower()
        ]
