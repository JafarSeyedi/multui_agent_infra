from pydantic import BaseModel
from typing import List, Optional, Dict


class Document(BaseModel):

    document_id: str

    title: Optional[str]

    source: Optional[str]

    metadata: Optional[Dict]

class DocumentChunk(BaseModel):

    chunk_id: str

    document_id: str

    text: str

    embedding: Optional[List[float]]

    metadata: Optional[Dict]
