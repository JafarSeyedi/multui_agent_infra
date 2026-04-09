from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Dict, List

from config.models.rag.rag_models import DocumentChunk

from .retriever_result import RetrievalResult
from .base_retriever import BaseRetriever

# ---------------------------------------------------------
# Keyword Retriever (BM25-style scoring)
# ---------------------------------------------------------
class BM25KeywordRetriever(BaseRetriever):
    """Dependency-light BM25 retriever backed by the document store cache."""

    def __init__(self, document_store) -> None:
        self.document_store = document_store
        self.index_built = False
        self.corpus_chunks: List[DocumentChunk] = []
        self.tokenized_corpus: List[List[str]] = []
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.term_freqs: List[Counter[str]] = []
        self.avg_doc_len: float = 0.0
        self.k1 = 1.5
        self.b = 0.75

    def invalidate(self) -> None:
        self.index_built = False

    def _ensure_index(self) -> None:
        current_chunks = list(self.document_store.chunks.values())
        if self.index_built and len(current_chunks) == len(self.corpus_chunks):
            return

        self.corpus_chunks = current_chunks
        self.tokenized_corpus = []
        self.doc_freqs = defaultdict(int)
        self.term_freqs = []

        total_terms = 0
        for chunk in self.corpus_chunks:
            tokens = self._tokenize(chunk.text)
            self.tokenized_corpus.append(tokens)
            tf = Counter(tokens)
            self.term_freqs.append(tf)
            total_terms += len(tokens)
            for token in tf:
                self.doc_freqs[token] += 1

        self.avg_doc_len = total_terms / max(1, len(self.corpus_chunks))
        self.index_built = True

    async def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        self._ensure_index()
        if not self.corpus_chunks:
            return []

        query_tokens = self._tokenize(query)
        scored = []
        total_docs = len(self.corpus_chunks)
        for index, (chunk, doc_tf) in enumerate(zip(self.corpus_chunks, self.term_freqs)):
            doc_len = len(self.tokenized_corpus[index])
            score = 0.0
            for token in query_tokens:
                term_freq = doc_tf.get(token, 0)
                if term_freq == 0:
                    continue
                doc_freq = self.doc_freqs.get(token, 0)
                idf = math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
                denom = term_freq + self.k1 * (1 - self.b + self.b * doc_len / (self.avg_doc_len or 1.0))
                score += idf * ((term_freq * (self.k1 + 1)) / (denom or 1.0))
            if score > 0:
                scored.append((chunk, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [
            RetrievalResult(
                chunk=chunk,
                score=score,
                source="keyword",
                meta={"keyword_raw_score": score},
            )
            for chunk, score in scored[:top_k]
        ]

    def _tokenize(self, text: str) -> List[str]:
        return [token.casefold() for token in text.split() if token.strip()]
