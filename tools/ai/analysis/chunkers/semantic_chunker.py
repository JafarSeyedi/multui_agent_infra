#!/usr/bin/env python3
"""
Semantic Chunker - AI Development Framework
Intelligently chunks text based on semantic boundaries and meaning.

Part of the Level 2 Analysis tools (chunkers/semantic_chunker.py)

This semantic_chunker.py provides:

1. Multiple Chunking Strategies - Similarity-based, LLM-based, topic segmentation, discourse markers, hybrid, and adaptive
2. Embedding Similarity - Uses Ollama embeddings to detect semantic boundaries
3. LLM-Powered Analysis - Leverages LLMs for intelligent boundary detection and classification
4. Topic Segmentation - Identifies topic shifts using embedding similarity
5. Discourse Marker Detection - Recognizes transition words and phrases
6. Entity Extraction - Identifies named entities in chunks
7. Chunk Summarization - Generates concise summaries using LLM
8. Coherence Scoring - Evaluates the quality of chunking
9. Relationship Building - Establishes connections between chunks
10. Adaptive Strategy - Automatically selects the best strategy based on content type

The semantic chunker provides the highest level of intelligence for chunking, making it ideal for complex documents and knowledge base construction.
"""

import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Iterator, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import numpy as np

from ...shared.logger import get_logger
from ...shared.llm_client import LLMClient
from ...level_2_analysis.encoders.ollama_encoder import OllamaEncoder, CodeChunk as EncodedChunk

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class SemanticChunkType(str, Enum):
    """Type of semantic chunk."""
    CONCEPT = "concept"               # Single coherent concept
    TOPIC_TRANSITION = "topic_transition"  # Transition between topics
    PROCEDURE = "procedure"           # Step-by-step procedure
    DEFINITION = "definition"         # Term definition
    COMPARISON = "comparison"         # Comparing multiple items
    CAUSE_EFFECT = "cause_effect"     # Cause and effect relationship
    PROBLEM_SOLUTION = "problem_solution"  # Problem and solution
    NARRATIVE = "narrative"           # Story or sequence
    ARGUMENT = "argument"             # Argument with evidence
    EXAMPLE = "example"               # Illustrative example
    SUMMARY = "summary"               # Summary or conclusion
    INTRODUCTION = "introduction"     # Introductory content
    TRANSITION = "transition"         # Transitional content
    DIGRESSION = "digression"         # Off-topic content
    UNKNOWN = "unknown"


class ChunkingStrategy(str, Enum):
    """Semantic chunking strategy."""
    SIMILARITY_BASED = "similarity_based"      # Based on embedding similarity
    LLM_BASED = "llm_based"                    # Using LLM for boundaries
    TOPIC_SEGMENTATION = "topic_segmentation"  # Topic modeling
    DISCOURSE_MARKERS = "discourse_markers"    # Using discourse markers
    HYBRID = "hybrid"                          # Combination of strategies
    ADAPTIVE = "adaptive"                      # Adapts to content type


class SimilarityMetric(str, Enum):
    """Similarity metric for chunking."""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class SemanticChunk:
    """A semantically coherent chunk of content."""
    id: str
    chunk_type: SemanticChunkType
    content: str
    source_id: Optional[str] = None  # ID of original chunk
    source_file: Optional[str] = None
    start_pos: int = 0
    end_pos: int = 0
    topic: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    entities: List[Dict[str, str]] = field(default_factory=list)  # {name, type}
    summary: Optional[str] = None
    embedding: Optional[List[float]] = None
    confidence: float = 1.0
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    relations: Dict[str, List[str]] = field(default_factory=dict)  # relation -> target chunk IDs
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()
        if not self.id:
            self.id = f"sem_{self.chunk_type.value}_{self.content_hash[:16]}"


@dataclass
class TopicSegment:
    """A topic segment identified in text."""
    topic_id: str
    topic_name: str
    start_idx: int
    end_idx: int
    confidence: float
    keywords: List[str]
    representative_chunks: List[str]  # Chunk IDs


@dataclass
class DiscourseMarker:
    """Discourse marker indicating structure."""
    marker: str
    marker_type: str  # 'transition', 'contrast', 'addition', 'cause', etc.
    position: int
    confidence: float


@dataclass
class SemanticChunkingResult:
    """Result of semantic chunking."""
    chunks: List[SemanticChunk]
    topics: List[TopicSegment]
    discourse_markers: List[DiscourseMarker]
    strategy_used: ChunkingStrategy
    original_chunks: int
    semantic_chunks: int
    avg_chunk_size: float
    coherence_score: float  # Overall coherence of chunks
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticChunkingConfig:
    """Configuration for semantic chunking."""
    strategy: ChunkingStrategy = ChunkingStrategy.HYBRID
    similarity_metric: SimilarityMetric = SimilarityMetric.COSINE
    similarity_threshold: float = 0.7
    min_chunk_sentences: int = 2
    max_chunk_sentences: int = 15
    target_chunk_tokens: int = 512
    overlap_sentences: int = 1
    use_embeddings: bool = True
    extract_topics: bool = True
    extract_entities: bool = True
    generate_summaries: bool = False
    detect_discourse_markers: bool = True
    preserve_original_boundaries: bool = False
    llm_model: Optional[str] = None  # For LLM-based chunking
    embedding_model: str = "mxbai-embed-large:latest"


# ============================================================
# DISCOURSE MARKERS
# ============================================================

class DiscourseMarkerDetector:
    """Detects discourse markers in text."""
    
    # Common discourse markers by type
    MARKERS = {
        'transition': [
            'however', 'therefore', 'thus', 'consequently', 'meanwhile',
            'subsequently', 'furthermore', 'moreover', 'nevertheless',
            'nonetheless', 'otherwise', 'alternatively'
        ],
        'contrast': [
            'but', 'however', 'although', 'though', 'whereas', 'while',
            'on the other hand', 'in contrast', 'conversely', 'yet',
            'still', 'despite', 'in spite of', 'unlike'
        ],
        'addition': [
            'and', 'also', 'additionally', 'furthermore', 'moreover',
            'besides', 'in addition', 'what is more', 'not only', 'as well as'
        ],
        'cause_effect': [
            'because', 'since', 'as', 'due to', 'owing to', 'thanks to',
            'as a result', 'consequently', 'hence', 'thus', 'therefore',
            'so', 'for this reason', 'accordingly'
        ],
        'exemplification': [
            'for example', 'for instance', 'such as', 'like', 'including',
            'namely', 'specifically', 'to illustrate', 'as an example'
        ],
        'conclusion': [
            'in conclusion', 'to conclude', 'in summary', 'to summarize',
            'overall', 'in brief', 'in short', 'finally', 'lastly'
        ],
        'sequence': [
            'first', 'second', 'third', 'firstly', 'secondly', 'thirdly',
            'next', 'then', 'after', 'before', 'finally', 'lastly',
            'initially', 'subsequently', 'eventually'
        ],
        'emphasis': [
            'indeed', 'in fact', 'actually', 'certainly', 'surely',
            'undoubtedly', 'clearly', 'obviously', 'importantly',
            'significantly', 'notably', 'especially', 'particularly'
        ],
        'reformulation': [
            'in other words', 'that is', 'i.e.', 'namely', 'to put it differently',
            'rather', 'more precisely', 'specifically'
        ]
    }
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.patterns = {}
        for marker_type, markers in self.MARKERS.items():
            pattern = r'\b(' + '|'.join(re.escape(m) for m in markers) + r')\b'
            self.patterns[marker_type] = re.compile(pattern, re.IGNORECASE)
    
    def detect(self, text: str) -> List[DiscourseMarker]:
        """Detect discourse markers in text."""
        markers = []
        
        for marker_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                marker = DiscourseMarker(
                    marker=match.group(1).lower(),
                    marker_type=marker_type,
                    position=match.start(),
                    confidence=0.9  # Could be adjusted based on context
                )
                markers.append(marker)
        
        return sorted(markers, key=lambda m: m.position)
    
    def get_boundary_scores(self, text: str, positions: List[int]) -> List[float]:
        """Score potential chunk boundaries based on discourse markers."""
        markers = self.detect(text)
        scores = [0.0] * len(positions)
        
        for i, pos in enumerate(positions):
            # Check markers near this position
            nearby_markers = [m for m in markers if abs(m.position - pos) < 100]
            
            for marker in nearby_markers:
                # Transition and conclusion markers are strong boundary indicators
                if marker.marker_type in ('transition', 'conclusion', 'sequence'):
                    scores[i] += 0.3
                elif marker.marker_type in ('contrast', 'reformulation'):
                    scores[i] += 0.2
                elif marker.marker_type in ('addition', 'exemplification'):
                    scores[i] -= 0.1  # These suggest continuity
            
            # Cap scores
            scores[i] = max(0.0, min(1.0, scores[i]))
        
        return scores


# ============================================================
# TOPIC SEGMENTATION
# ============================================================

class TopicSegmenter:
    """Identifies topic segments using embedding similarity."""
    
    def __init__(self, encoder: Optional[OllamaEncoder] = None):
        self.encoder = encoder
        self.marker_detector = DiscourseMarkerDetector()
    
    def segment(self, 
                sentences: List[str],
                embeddings: Optional[List[List[float]]] = None) -> List[TopicSegment]:
        """Segment text into topics."""
        if len(sentences) < 3:
            return []
        
        # Get embeddings if not provided
        if embeddings is None and self.encoder:
            embeddings = []
            for sent in sentences:
                emb = self.encoder.encode_single(sent)
                embeddings.append(emb if emb else [0.0] * 1024)
        
        if not embeddings:
            return []
        
        # Calculate similarity between consecutive sentences
        similarities = []
        for i in range(len(sentences) - 1):
            if embeddings[i] and embeddings[i + 1]:
                sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
                similarities.append(sim)
            else:
                similarities.append(0.5)
        
        # Detect topic boundaries (low similarity)
        threshold = np.mean(similarities) - 0.5 * np.std(similarities) if similarities else 0.5
        boundaries = [0]
        
        for i, sim in enumerate(similarities):
            if sim < threshold:
                boundaries.append(i + 1)
        
        boundaries.append(len(sentences))
        
        # Create topic segments
        segments = []
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            
            if end - start >= 2:  # At least 2 sentences
                segment_sentences = sentences[start:end]
                
                # Extract keywords
                keywords = self._extract_keywords(' '.join(segment_sentences))
                
                # Generate topic name
                topic_name = self._generate_topic_name(segment_sentences, keywords)
                
                segment = TopicSegment(
                    topic_id=f"topic_{i:03d}",
                    topic_name=topic_name,
                    start_idx=start,
                    end_idx=end - 1,
                    confidence=0.8,
                    keywords=keywords,
                    representative_chunks=[]
                )
                segments.append(segment)
        
        return segments
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity."""
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
    
    def _extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """Extract keywords from text."""
        # Simple TF-based keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Count frequencies
        from collections import Counter
        word_counts = Counter(words)
        
        # Filter stopwords
        stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'are', 'was', 'were'}
        for sw in stopwords:
            word_counts.pop(sw, None)
        
        # Return top keywords
        return [word for word, _ in word_counts.most_common(top_k)]
    
    def _generate_topic_name(self, sentences: List[str], keywords: List[str]) -> str:
        """Generate a name for the topic."""
        if keywords:
            return ' & '.join(keywords[:3]).title()
        
        # Use first sentence as fallback
        if sentences:
            first = sentences[0][:50]
            return first + ('...' if len(sentences[0]) > 50 else '')
        
        return "Unknown Topic"


# ============================================================
# MAIN SEMANTIC CHUNKER
# ============================================================

class SemanticChunker:
    """
    Intelligent semantic chunking using multiple strategies.
    
    Features:
    - Embedding similarity-based chunking
    - LLM-powered boundary detection
    - Topic segmentation
    - Discourse marker analysis
    - Hybrid/adaptive strategies
    - Entity extraction
    - Chunk summarization
    - Coherence scoring
    - Overlap management
    """
    
    def __init__(self, config: Optional[SemanticChunkingConfig] = None):
        self.config = config or SemanticChunkingConfig()
        self.encoder: Optional[OllamaEncoder] = None
        self.llm: Optional[LLMClient] = None
        self.topic_segmenter = TopicSegmenter()
        self.marker_detector = DiscourseMarkerDetector()
        
        if self.config.use_embeddings:
            self.encoder = OllamaEncoder(model=self.config.embedding_model)
        
        if self.config.strategy in (ChunkingStrategy.LLM_BASED, ChunkingStrategy.HYBRID):
            self.llm = LLMClient()
        
        # Connect topic segmenter to encoder
        if self.encoder:
            self.topic_segmenter.encoder = self.encoder
    
    # ============================================================
    # PUBLIC API
    # ============================================================
    
    def chunk(self, 
              text: str,
              source_id: Optional[str] = None,
              source_file: Optional[str] = None) -> SemanticChunkingResult:
        """Perform semantic chunking on text."""
        import time
        start_time = time.time()
        
        logger.info(f"Semantic chunking text of length {len(text)}")
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        if len(sentences) < self.config.min_chunk_sentences:
            # Text too short, return as single chunk
            chunk = self._create_single_chunk(text, sentences, source_id, source_file)
            return SemanticChunkingResult(
                chunks=[chunk],
                topics=[],
                discourse_markers=[],
                strategy_used=self.config.strategy,
                original_chunks=1,
                semantic_chunks=1,
                avg_chunk_size=len(sentences),
                coherence_score=1.0,
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        # Choose chunking strategy
        if self.config.strategy == ChunkingStrategy.SIMILARITY_BASED:
            chunks, boundaries = self._similarity_based_chunking(sentences)
        elif self.config.strategy == ChunkingStrategy.LLM_BASED:
            chunks, boundaries = self._llm_based_chunking(sentences)
        elif self.config.strategy == ChunkingStrategy.TOPIC_SEGMENTATION:
            chunks, boundaries = self._topic_based_chunking(sentences)
        elif self.config.strategy == ChunkingStrategy.DISCOURSE_MARKERS:
            chunks, boundaries = self._discourse_based_chunking(sentences)
        elif self.config.strategy == ChunkingStrategy.HYBRID:
            chunks, boundaries = self._hybrid_chunking(sentences)
        else:  # ADAPTIVE
            chunks, boundaries = self._adaptive_chunking(sentences)
        
        # Extract topics
        topics = []
        if self.config.extract_topics:
            topics = self.topic_segmenter.segment(sentences)
            
            # Link chunks to topics
            for chunk in chunks:
                chunk_topic = self._assign_topic_to_chunk(chunk, topics)
                if chunk_topic:
                    chunk.topic = chunk_topic.topic_name
                    chunk.metadata['topic_id'] = chunk_topic.topic_id
        
        # Extract entities
        if self.config.extract_entities:
            for chunk in chunks:
                chunk.entities = self._extract_entities(chunk.content)
        
        # Generate summaries
        if self.config.generate_summaries and self.llm:
            for chunk in chunks:
                chunk.summary = self._generate_summary(chunk.content)
        
        # Detect discourse markers
        discourse_markers = []
        if self.config.detect_discourse_markers:
            discourse_markers = self.marker_detector.detect(text)
        
        # Calculate coherence score
        coherence_score = self._calculate_coherence(chunks)
        
        # Build relationships
        chunks = self._build_chunk_relationships(chunks)
        
        processing_time = (time.time() - start_time) * 1000
        
        result = SemanticChunkingResult(
            chunks=chunks,
            topics=topics,
            discourse_markers=discourse_markers,
            strategy_used=self.config.strategy,
            original_chunks=1,
            semantic_chunks=len(chunks),
            avg_chunk_size=sum(len(c.content.split()) for c in chunks) / len(chunks),
            coherence_score=coherence_score,
            processing_time_ms=processing_time
        )
        
        logger.info(f"Created {len(chunks)} semantic chunks in {processing_time:.1f}ms")
        return result
    
    def chunk_documents(self, 
                        documents: List[Tuple[str, str, str]],  # (text, source_id, source_file)
                        batch_size: int = 10) -> List[SemanticChunkingResult]:
        """Chunk multiple documents."""
        results = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            for text, source_id, source_file in batch:
                result = self.chunk(text, source_id, source_file)
                results.append(result)
            
            logger.info(f"Processed batch {i // batch_size + 1}, total chunks: {sum(r.semantic_chunks for r in results)}")
        
        return results
    
    def merge_related_chunks(self, chunks: List[SemanticChunk], threshold: float = 0.8) -> List[SemanticChunk]:
        """Merge semantically related chunks."""
        if len(chunks) < 2 or not self.encoder:
            return chunks
        
        # Get embeddings
        for chunk in chunks:
            if not chunk.embedding:
                chunk.embedding = self.encoder.encode_single(chunk.content)
        
        # Group by similarity
        merged = []
        used = set()
        
        for i, chunk in enumerate(chunks):
            if i in used:
                continue
            
            group = [chunk]
            used.add(i)
            
            for j, other in enumerate(chunks):
                if j in used or i == j:
                    continue
                
                if chunk.embedding and other.embedding:
                    sim = self._cosine_similarity(chunk.embedding, other.embedding)
                    if sim >= threshold:
                        group.append(other)
                        used.add(j)
            
            if len(group) > 1:
                merged_chunk = self._merge_chunk_group(group)
                merged.append(merged_chunk)
            else:
                merged.append(chunk)
        
        return merged
    
    # ============================================================
    # CHUNKING STRATEGIES
    # ============================================================
    
    def _similarity_based_chunking(self, sentences: List[str]) -> Tuple[List[SemanticChunk], List[int]]:
        """Chunk based on embedding similarity."""
        chunks = []
        boundaries = [0]
        
        if not self.encoder:
            return self._fallback_chunking(sentences)
        
        # Get embeddings
        embeddings = []
        for sent in sentences:
            emb = self.encoder.encode_single(sent)
            embeddings.append(emb if emb else [0.0] * 1024)
        
        # Calculate similarities
        current_chunk = [sentences[0]]
        current_start = 0
        
        for i in range(1, len(sentences)):
            # Similarity with previous sentence
            sim_prev = self._cosine_similarity(embeddings[i - 1], embeddings[i])
            
            # Similarity with chunk average
            if len(current_chunk) > 0:
                chunk_emb = self._average_embedding(embeddings[current_start:i])
                sim_chunk = self._cosine_similarity(chunk_emb, embeddings[i])
            else:
                sim_chunk = sim_prev
            
            # Decision: continue or break
            should_break = False
            
            if sim_prev < self.config.similarity_threshold * 0.8:
                should_break = True
            elif sim_chunk < self.config.similarity_threshold:
                should_break = True
            elif len(current_chunk) >= self.config.max_chunk_sentences:
                should_break = True
            
            if should_break and len(current_chunk) >= self.config.min_chunk_sentences:
                # Create chunk
                chunk = self._create_chunk_from_sentences(
                    current_chunk, current_start, i - 1, sentences
                )
                chunks.append(chunk)
                boundaries.append(i)
                
                # Start new chunk with overlap
                overlap = min(self.config.overlap_sentences, len(current_chunk))
                if overlap > 0:
                    current_chunk = current_chunk[-overlap:] + [sentences[i]]
                    current_start = i - overlap
                else:
                    current_chunk = [sentences[i]]
                    current_start = i
            else:
                current_chunk.append(sentences[i])
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk_from_sentences(
                current_chunk, current_start, len(sentences) - 1, sentences
            )
            chunks.append(chunk)
            boundaries.append(len(sentences))
        
        return chunks, boundaries
    
    def _llm_based_chunking(self, sentences: List[str]) -> Tuple[List[SemanticChunk], List[int]]:
        """Use LLM to identify semantic boundaries."""
        if not self.llm:
            return self._similarity_based_chunking(sentences)
        
        # Prepare text with sentence markers
        marked_text = ""
        for i, sent in enumerate(sentences):
            marked_text += f"[{i}] {sent}\n"
        
        prompt = f"""
        Analyze the following text and identify natural semantic boundaries.
        The text has sentence numbers in brackets.
        
        Return a JSON object with:
        - boundaries: List of sentence indices where a new semantic chunk should start
        - chunk_types: List of semantic types for each chunk (choose from: concept, procedure, definition, 
          comparison, cause_effect, problem_solution, narrative, argument, example, summary, introduction)
        - reasoning: Brief explanation of the chunking decisions
        
        Text:
        {marked_text[:4000]}  # Limit for context window
        
        Guidelines:
        - Chunks should be 2-15 sentences
        - Break at topic shifts, transitions, or logical boundaries
        - Keep related content together
        """
        
        try:
            response = self.llm.complete_json(prompt)
            boundaries = response.get('boundaries', [0])
            chunk_types = response.get('chunk_types', ['unknown'])
            
            # Ensure 0 is first boundary
            if 0 not in boundaries:
                boundaries.insert(0, 0)
            
            # Create chunks
            chunks = []
            for i in range(len(boundaries)):
                start = boundaries[i]
                end = boundaries[i + 1] if i + 1 < len(boundaries) else len(sentences)
                
                chunk_sentences = sentences[start:end]
                if chunk_sentences:
                    chunk_type = SemanticChunkType.UNKNOWN
                    if i < len(chunk_types):
                        try:
                            chunk_type = SemanticChunkType(chunk_types[i])
                        except ValueError:
                            pass
                    
                    chunk = self._create_chunk_from_sentences(
                        chunk_sentences, start, end - 1, sentences, chunk_type
                    )
                    chunk.metadata['llm_reasoning'] = response.get('reasoning', '')
                    chunks.append(chunk)
            
            return chunks, boundaries
            
        except Exception as e:
            logger.warning(f"LLM chunking failed: {e}, falling back to similarity")
            return self._similarity_based_chunking(sentences)
    
    def _topic_based_chunking(self, sentences: List[str]) -> Tuple[List[SemanticChunk], List[int]]:
        """Chunk based on topic segmentation."""
        # Get topic segments
        segments = self.topic_segmenter.segment(sentences)
        
        chunks = []
        boundaries = [0]
        
        for segment in segments:
            chunk_sentences = sentences[segment.start_idx:segment.end_idx + 1]
            
            chunk = self._create_chunk_from_sentences(
                chunk_sentences, segment.start_idx, segment.end_idx, sentences
            )
            chunk.topic = segment.topic_name
            chunk.keywords = segment.keywords
            chunk.metadata['topic_id'] = segment.topic_id
            chunk.metadata['topic_confidence'] = segment.confidence
            
            chunks.append(chunk)
            boundaries.append(segment.end_idx + 1)
        
        return chunks, boundaries
    
    def _discourse_based_chunking(self, sentences: List[str]) -> Tuple[List[SemanticChunk], List[int]]:
        """Chunk using discourse markers."""
        # Build full text to detect markers
        full_text = ' '.join(sentences)
        sentence_starts = []
        pos = 0
        for sent in sentences:
            sentence_starts.append(pos)
            pos += len(sent) + 1  # +1 for space
        
        # Get boundary scores
        scores = self.marker_detector.get_boundary_scores(full_text, sentence_starts)
        
        # Find boundaries with high scores
        threshold = 0.3
        boundaries = [0]
        
        for i, score in enumerate(scores):
            if score >= threshold and i > 0:
                # Check if chunk would be valid size
                last_boundary = boundaries[-1]
                if i - last_boundary >= self.config.min_chunk_sentences:
                    boundaries.append(i)
        
        boundaries.append(len(sentences))
        
        # Create chunks
        chunks = []
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            chunk_sentences = sentences[start:end]
            
            # Determine chunk type from nearby markers
            chunk_type = self._infer_chunk_type_from_markers(full_text, start, end, sentence_starts)
            
            chunk = self._create_chunk_from_sentences(
                chunk_sentences, start, end - 1, sentences, chunk_type
            )
            chunks.append(chunk)
        
        return chunks, boundaries
    
    def _hybrid_chunking(self, sentences: List[str]) -> Tuple[List[SemanticChunk], List[int]]:
        """Combine multiple strategies."""
        # Get boundaries from different strategies
        _, sim_boundaries = self._similarity_based_chunking(sentences)
        _, discourse_boundaries = self._discourse_based_chunking(sentences)
        
        # Try topic segmentation
        topics = self.topic_segmenter.segment(sentences)
        topic_boundaries = [0] + [t.start_idx for t in topics] + [len(sentences)]
        
        # Combine boundaries with voting
        all_boundaries = set(sim_boundaries) | set(discourse_boundaries) | set(topic_boundaries)
        boundaries = sorted([b for b in all_boundaries if b < len(sentences)])
        
        if 0 not in boundaries:
            boundaries.insert(0, 0)
        if len(sentences) not in boundaries:
            boundaries.append(len(sentences))
        
        # Filter boundaries that would create invalid chunks
        filtered_boundaries = [0]
        for b in boundaries[1:-1]:
            last = filtered_boundaries[-1]
            if b - last >= self.config.min_chunk_sentences:
                filtered_boundaries.append(b)
        filtered_boundaries.append(len(sentences))
        
        # Create chunks
        chunks = []
        for i in range(len(filtered_boundaries) - 1):
            start = filtered_boundaries[i]
            end = filtered_boundaries[i + 1]
            chunk_sentences = sentences[start:end]
            
            # Use LLM for type classification if available
            chunk_type = SemanticChunkType.UNKNOWN
            if self.llm and len(chunk_sentences) > 0:
                chunk_type = self._classify_chunk_type_llm(' '.join(chunk_sentences))
            
            chunk = self._create_chunk_from_sentences(
                chunk_sentences, start, end - 1, sentences, chunk_type
            )
            chunks.append(chunk)
        
        return chunks, filtered_boundaries
    
    def _adaptive_chunking(self, sentences: List[str]) -> Tuple[List[SemanticChunk], List[int]]:
        """Adapt strategy based on content characteristics."""
        # Analyze content
        text = ' '.join(sentences)
        content_type = self._analyze_content_type(text)
        
        # Choose strategy based on content type
        if content_type == 'technical':
            return self._similarity_based_chunking(sentences)
        elif content_type == 'narrative':
            return self._discourse_based_chunking(sentences)
        elif content_type == 'expository':
            return self._topic_based_chunking(sentences)
        else:
            return self._hybrid_chunking(sentences)
    
    def _fallback_chunking(self, sentences: List[str]) -> Tuple[List[SemanticChunk], List[int]]:
        """Simple fallback chunking."""
        chunks = []
        boundaries = [0]
        
        for i in range(0, len(sentences), self.config.max_chunk_sentences):
            end = min(i + self.config.max_chunk_sentences, len(sentences))
            chunk_sentences = sentences[i:end]
            
            chunk = self._create_chunk_from_sentences(chunk_sentences, i, end - 1, sentences)
            chunks.append(chunk)
            boundaries.append(end)
        
        return chunks, boundaries
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Basic sentence splitting
        pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(pattern, text)
        
        # Clean and filter
        cleaned = []
        for sent in sentences:
            sent = sent.strip()
            if sent:
                cleaned.append(sent)
        
        return cleaned
    
    def _create_single_chunk(self, text: str, sentences: List[str],
                             source_id: Optional[str], source_file: Optional[str]) -> SemanticChunk:
        """Create a single chunk from short text."""
        return SemanticChunk(
            chunk_type=SemanticChunkType.UNKNOWN,
            content=text,
            source_id=source_id,
            source_file=source_file,
            start_pos=0,
            end_pos=len(text),
            metadata={
                'sentence_count': len(sentences),
                'is_single_chunk': True
            }
        )
    
    def _create_chunk_from_sentences(self, sentences: List[str], start_idx: int, end_idx: int,
                                      all_sentences: List[str],
                                      chunk_type: SemanticChunkType = SemanticChunkType.UNKNOWN) -> SemanticChunk:
        """Create a chunk from sentence list."""
        content = ' '.join(sentences)
        
        # Calculate absolute positions
        start_pos = len(' '.join(all_sentences[:start_idx]))
        if start_pos > 0:
            start_pos += 1  # Account for space
        end_pos = start_pos + len(content)
        
        return SemanticChunk(
            chunk_type=chunk_type,
            content=content,
            start_pos=start_pos,
            end_pos=end_pos,
            metadata={
                'sentence_count': len(sentences),
                'start_sentence': start_idx,
                'end_sentence': end_idx
            }
        )
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity."""
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
    
    def _average_embedding(self, embeddings: List[List[float]]) -> List[float]:
        """Calculate average embedding."""
        if not embeddings:
            return []
        
        import numpy as np
        avg = np.mean(embeddings, axis=0)
        return avg.tolist()
    
    def _analyze_content_type(self, text: str) -> str:
        """Analyze content type (technical, narrative, expository)."""
        text_lower = text.lower()
        
        # Technical indicators
        tech_indicators = ['function', 'class', 'method', 'api', 'code', 'implementation',
                          'algorithm', 'data', 'system', 'interface', 'module']
        tech_score = sum(1 for word in tech_indicators if word in text_lower)
        
        # Narrative indicators
        narrative_indicators = ['story', 'happened', 'then', 'after', 'before', 'said',
                               'felt', 'thought', 'remember', 'once', 'day']
        narrative_score = sum(1 for word in narrative_indicators if word in text_lower)
        
        # Expository indicators
        expository_indicators = ['explain', 'describe', 'therefore', 'because', 'however',
                                'furthermore', 'consequently', 'analysis', 'conclusion']
        expository_score = sum(1 for word in expository_indicators if word in text_lower)
        
        scores = {'technical': tech_score, 'narrative': narrative_score, 'expository': expository_score}
        return max(scores, key=scores.get)
    
    def _classify_chunk_type_llm(self, text: str) -> SemanticChunkType:
        """Use LLM to classify chunk type."""
        if not self.llm:
            return SemanticChunkType.UNKNOWN
        
        prompt = f"""
        Classify the following text into one of these semantic types:
        concept, procedure, definition, comparison, cause_effect, problem_solution,
        narrative, argument, example, summary, introduction
        
        Return only the type name.
        
        Text: {text[:500]}
        """
        
        try:
            response = self.llm.complete(prompt).strip().lower()
            return SemanticChunkType(response)
        except:
            return SemanticChunkType.UNKNOWN
    
    def _infer_chunk_type_from_markers(self, text: str, start_idx: int, end_idx: int,
                                        sentence_starts: List[int]) -> SemanticChunkType:
        """Infer chunk type from nearby discourse markers."""
        markers = self.marker_detector.detect(text)
        
        start_pos = sentence_starts[start_idx] if start_idx < len(sentence_starts) else 0
        end_pos = sentence_starts[end_idx - 1] if end_idx <= len(sentence_starts) else len(text)
        
        nearby = [m for m in markers if start_pos - 50 <= m.position <= end_pos + 50]
        
        marker_types = [m.marker_type for m in nearby]
        
        if 'exemplification' in marker_types:
            return SemanticChunkType.EXAMPLE
        elif 'cause_effect' in marker_types:
            return SemanticChunkType.CAUSE_EFFECT
        elif 'contrast' in marker_types:
            return SemanticChunkType.COMPARISON
        elif 'conclusion' in marker_types:
            return SemanticChunkType.SUMMARY
        elif 'sequence' in marker_types:
            return SemanticChunkType.PROCEDURE
        
        return SemanticChunkType.CONCEPT
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities from text."""
        # Simple rule-based extraction
        entities = []
        
        # Capitalized phrases (potential proper nouns)
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        for match in re.finditer(pattern, text):
            entity_text = match.group()
            if len(entity_text) > 2 and entity_text.lower() not in ('The', 'This', 'That', 'These', 'Those'):
                # Simple type inference
                entity_type = 'unknown'
                if any(tech in entity_text.lower() for tech in ['Inc', 'Corp', 'LLC', 'Ltd']):
                    entity_type = 'organization'
                elif any(month in entity_text for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']):
                    entity_type = 'date'
                
                entities.append({'name': entity_text, 'type': entity_type})
        
        return entities[:10]  # Limit
    
    def _generate_summary(self, text: str) -> Optional[str]:
        """Generate summary using LLM."""
        if not self.llm or len(text) < 100:
            return None
        
        prompt = f"""
        Summarize the following text in one concise sentence (max 50 words):
        
        {text[:1000]}
        """
        
        try:
            return self.llm.complete(prompt).strip()
        except:
            return None
    
    def _calculate_coherence(self, chunks: List[SemanticChunk]) -> float:
        """Calculate overall coherence score."""
        if len(chunks) < 2 or not self.encoder:
            return 1.0
        
        # Get embeddings
        for chunk in chunks:
            if not chunk.embedding:
                chunk.embedding = self.encoder.encode_single(chunk.content)
        
        # Calculate average similarity between consecutive chunks
        similarities = []
        for i in range(len(chunks) - 1):
            if chunks[i].embedding and chunks[i + 1].embedding:
                sim = self._cosine_similarity(chunks[i].embedding, chunks[i + 1].embedding)
                similarities.append(sim)
        
        if similarities:
            # Lower similarity means better separation (higher coherence)
            return 1.0 - (sum(similarities) / len(similarities))
        
        return 0.5
    
    def _build_chunk_relationships(self, chunks: List[SemanticChunk]) -> List[SemanticChunk]:
        """Build relationships between chunks."""
        if len(chunks) < 2:
            return chunks
        
        for i, chunk in enumerate(chunks):
            # Sequential relationships
            if i > 0:
                chunk.relations.setdefault('preceded_by', []).append(chunks[i - 1].id)
            if i < len(chunks) - 1:
                chunk.relations.setdefault('followed_by', []).append(chunks[i + 1].id)
            
            # Hierarchical relationships
            if chunk.parent_id:
                for other in chunks:
                    if other.id == chunk.parent_id:
                        if chunk.id not in other.children_ids:
                            other.children_ids.append(chunk.id)
        
        return chunks
    
    def _merge_chunk_group(self, chunks: List[SemanticChunk]) -> SemanticChunk:
        """Merge a group of related chunks."""
        if not chunks:
            raise ValueError("Cannot merge empty chunk group")
        
        # Sort by position
        sorted_chunks = sorted(chunks, key=lambda c: c.start_pos)
        
        # Combine content
        content_parts = [c.content for c in sorted_chunks]
        merged_content = ' '.join(content_parts)
        
        # Determine primary type (most common)
        type_counts = defaultdict(int)
        for c in chunks:
            type_counts[c.chunk_type] += 1
        primary_type = max(type_counts, key=type_counts.get)
        
        # Combine metadata
        merged_metadata = {
            'merged_from': [c.id for c in chunks],
            'original_types': [c.chunk_type.value for c in chunks],
            'total_sentences': sum(c.metadata.get('sentence_count', 0) for c in chunks)
        }
        
        return SemanticChunk(
            chunk_type=primary_type,
            content=merged_content,
            source_id=chunks[0].source_id,
            source_file=chunks[0].source_file,
            start_pos=sorted_chunks[0].start_pos,
            end_pos=sorted_chunks[-1].end_pos,
            topic=chunks[0].topic,
            keywords=list(set().union(*[c.keywords for c in chunks])),
            entities=list({e['name']: e for c in chunks for e in c.entities}.values()),
            metadata=merged_metadata
        )
    
    def _assign_topic_to_chunk(self, chunk: SemanticChunk,
                                topics: List[TopicSegment]) -> Optional[TopicSegment]:
        """Assign a topic segment to a chunk."""
        chunk_start = chunk.metadata.get('start_sentence', 0)
        chunk_end = chunk.metadata.get('end_sentence', 0)
        
        for topic in topics:
            # Check if chunk overlaps with topic
            if (topic.start_idx <= chunk_end and topic.end_idx >= chunk_start):
                return topic
        
        return None
    
    # ============================================================
    # EXPORT
    # ============================================================
    
    def export_result_json(self, result: SemanticChunkingResult,
                           output_path: Optional[Path] = None) -> str:
        """Export chunking result as JSON."""
        data = {
            'strategy_used': result.strategy_used.value,
            'original_chunks': result.original_chunks,
            'semantic_chunks': result.semantic_chunks,
            'avg_chunk_size': result.avg_chunk_size,
            'coherence_score': result.coherence_score,
            'processing_time_ms': result.processing_time_ms,
            'topics': [
                {
                    'topic_id': t.topic_id,
                    'topic_name': t.topic_name,
                    'start_idx': t.start_idx,
                    'end_idx': t.end_idx,
                    'confidence': t.confidence,
                    'keywords': t.keywords
                }
                for t in result.topics
            ],
            'discourse_markers': [
                {
                    'marker': m.marker,
                    'type': m.marker_type,
                    'position': m.position,
                    'confidence': m.confidence
                }
                for m in result.discourse_markers[:50]  # Limit
            ],
            'chunks': [
                {
                    'id': c.id,
                    'type': c.chunk_type.value,
                    'content': c.content,
                    'source_id': c.source_id,
                    'source_file': c.source_file,
                    'topic': c.topic,
                    'keywords': c.keywords,
                    'entities': c.entities,
                    'summary': c.summary,
                    'confidence': c.confidence,
                    'parent_id': c.parent_id,
                    'children_ids': c.children_ids,
                    'relations': c.relations,
                    'content_hash': c.content_hash,
                    'metadata': c.metadata
                }
                for c in result.chunks
            ]
        }
        
        json_str = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(json_str)
        
        return json_str
    
    def export_for_embedding(self, chunks: List[SemanticChunk]) -> List[Dict[str, Any]]:
        """Export chunks in format ready for embedding."""
        return [
            {
                'id': c.id,
                'text': self._format_for_embedding(c),
                'metadata': {
                    'type': c.chunk_type.value,
                    'source_file': c.source_file,
                    'topic': c.topic,
                    'keywords': c.keywords,
                    'entities': [e['name'] for e in c.entities],
                    'summary': c.summary,
                    **c.metadata
                }
            }
            for c in chunks
        ]
    
    def _format_for_embedding(self, chunk: SemanticChunk) -> str:
        """Format chunk for optimal embedding."""
        parts = []
        
        if chunk.topic:
            parts.append(f"Topic: {chunk.topic}")
        
        if chunk.keywords:
            parts.append(f"Keywords: {', '.join(chunk.keywords)}")
        
        if chunk.summary:
            parts.append(f"Summary: {chunk.summary}")
        
        parts.append(chunk.content)
        
        return '\n'.join(parts)


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for semantic chunker."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Semantic chunking of text")
    parser.add_argument("input", type=Path, help="Input text file")
    parser.add_argument("--output", "-o", type=Path, help="Output JSON file")
    parser.add_argument("--strategy", choices=[s.value for s in ChunkingStrategy],
                       default=ChunkingStrategy.HYBRID.value, help="Chunking strategy")
    parser.add_argument("--threshold", type=float, default=0.7,
                       help="Similarity threshold for boundary detection")
    parser.add_argument("--min-sentences", type=int, default=2,
                       help="Minimum sentences per chunk")
    parser.add_argument("--max-sentences", type=int, default=15,
                       help="Maximum sentences per chunk")
    parser.add_argument("--embedding-model", default="mxbai-embed-large:latest",
                       help="Ollama embedding model")
    parser.add_argument("--no-embeddings", action="store_true",
                       help="Disable embedding-based features")
    parser.add_argument("--extract-topics", action="store_true",
                       help="Extract topic segments")
    parser.add_argument("--generate-summaries", action="store_true",
                       help="Generate chunk summaries")
    
    args = parser.parse_args()
    
    config = SemanticChunkingConfig(
        strategy=ChunkingStrategy(args.strategy),
        similarity_threshold=args.threshold,
        min_chunk_sentences=args.min_sentences,
        max_chunk_sentences=args.max_sentences,
        use_embeddings=not args.no_embeddings,
        extract_topics=args.extract_topics,
        generate_summaries=args.generate_summaries,
        embedding_model=args.embedding_model
    )
    
    chunker = SemanticChunker(config)
    
    # Read input
    text = args.input.read_text(encoding='utf-8')
    
    # Chunk
    result = chunker.chunk(text, source_file=str(args.input))
    
    # Output
    json_str = chunker.export_result_json(result, args.output)
    
    if not args.output:
        print(json_str)
    else:
        print(f"Result saved to {args.output}")
        print(f"Created {result.semantic_chunks} chunks in {result.processing_time_ms:.1f}ms")
        print(f"Coherence score: {result.coherence_score:.3f}")


if __name__ == "__main__":
    main()