"""Generic text chunking utilities used by the ingestion layer.

This module takes the `(text, meta)` tuples emitted by loader classes and
produces `Chunk` objects whose length sits inside sensible token boundaries.
Splitting behaviour is driven entirely by external *chunk rules* defined in
`chunk_rules.yml`.
"""

from __future__ import annotations

import re
import uuid
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Dict, List, Callable
import yaml

# --------------------------------------------------------------------------- #
# Data Classes
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Chunk:
    """Atomic piece of text sent to the embedder."""
    id: str
    doc_id: str
    text: str
    meta: dict[str, Any]
    
    # Additional fields for RAG system optimization
    chunk_index: int = 0
    overlap_tokens: int = 0
    token_count: int = 0


@dataclass(frozen=True, slots=True)
class ChunkRule:
    """Configuration for how to chunk a specific document type."""
    strategy: str
    min_tokens: int
    max_tokens: int
    overlap: int = 0
    
    def __post_init__(self):
        """Validate rule parameters."""
        if self.min_tokens < 0 or self.max_tokens < 0:
            raise ValueError("Token limits must be non-negative")
        if self.min_tokens > self.max_tokens and self.max_tokens > 0:
            raise ValueError("min_tokens cannot exceed max_tokens")
        if self.overlap < 0:
            raise ValueError("Overlap must be non-negative")


# --------------------------------------------------------------------------- #
# Token Counter Interface
# --------------------------------------------------------------------------- #


class TokenCounter:
    """Pluggable token counter for different tokenization strategies."""
    
    @staticmethod
    def simple_whitespace(text: str) -> int:
        """Count tokens by whitespace splitting (default)."""
        return len(text.split())
    
    @staticmethod
    def estimate_gpt(text: str) -> int:
        """Estimate GPT-style tokens (roughly 4 chars per token)."""
        # More accurate than whitespace for LLM tokenizers
        return max(1, len(text) // 4)


# --------------------------------------------------------------------------- #
# BaseChunker
# --------------------------------------------------------------------------- #


class BaseChunker:
    """Rule-driven splitter producing Chunk instances optimized for RAG."""
    
    # Class-level compiled regex for efficiency
    EMAIL_REPLY_PATTERNS = [
        re.compile(r'^>\s+', re.MULTILINE),
        re.compile(r'^On\s.+wrote:\s*$', re.MULTILINE | re.IGNORECASE),
        re.compile(r'^From:\s*.*$', re.MULTILINE | re.IGNORECASE),
        re.compile(r'^[-─]{3,}\s*Original Message\s*[-─]{3,}', re.MULTILINE | re.IGNORECASE)
    ]
    
    # Registry for splitting strategies
    _strategy_registry: Dict[str, Callable] = {}
    
    def __init__(self, rules_path: Optional[Path] = None, 
                 token_counter: Optional[Callable] = None) -> None:
        """Initialize chunker with rules and token counting strategy."""
        self.rules_path = rules_path or Path(__file__).with_name("chunk_rules.yml")
        self.token_counter = token_counter or TokenCounter.simple_whitespace
        
        # Load rules once
        self._rules: Dict[str, ChunkRule] = {}
        self._default_rule = ChunkRule(
            strategy="by_paragraph",
            min_tokens=50,
            max_tokens=300,
            overlap=20
        )
        self._load_rules()
        
        # Register default strategies
        self._register_default_strategies()
    
    def _load_rules(self) -> None:
        """Load chunking rules from YAML file."""
        if not self.rules_path.exists():
            return
            
        try:
            with self.rules_path.open() as f:
                raw_rules = yaml.safe_load(f) or {}
            
            for doc_type, config in raw_rules.items():
                try:
                    self._rules[doc_type.lower()] = ChunkRule(**config)
                except (TypeError, ValueError) as e:
                    # Log error and skip invalid rules
                    print(f"Warning: Invalid rule for {doc_type}: {e}")
        except Exception as e:
            print(f"Warning: Could not load rules from {self.rules_path}: {e}")
    
    def _register_default_strategies(self) -> None:
        """Register built-in splitting strategies."""
        self.register_strategy("by_paragraph", self._split_by_paragraph)
        self.register_strategy("by_slide", self._split_by_slide)
        self.register_strategy("by_email_block", self._split_by_email_block)
        self.register_strategy("by_email_thread", self._split_by_email_thread)
        self.register_strategy("split_on_blank_lines", self._split_by_paragraph)
        self.register_strategy("by_sentence", self._split_by_sentence)
    
    @classmethod
    def register_strategy(cls, name: str, func: Callable[[str], List[str]]) -> None:
        """Register a new splitting strategy."""
        cls._strategy_registry[name] = func
    
    # ---------------- API ---------------- #
    
    def split(self, text: str, meta: dict[str, Any]) -> List[Chunk]:
        """Split text into chunks according to document type rules."""
        if not text:
            return []
        
        # Get document info
        doc_type = meta.get("doc_type", "").lower()
        doc_id = meta.get("doc_id", uuid.uuid4().hex)
        
        # Select rule
        rule = self._rules.get(doc_type, self._default_rule)
        
        # Process text
        raw_segments = self._initial_split(text, rule.strategy)
        bounded_segments = self._enforce_bounds(raw_segments, rule)
        chunks = self._apply_overlap_and_wrap(bounded_segments, meta, rule, doc_id)
        
        return chunks
    
    # --------------- Split Strategies --------------- #
    
    def _split_by_paragraph(self, text: str) -> List[str]:
        """Split text on double newlines (paragraphs)."""
        # Handle different paragraph separators
        text = re.sub(r'\r\n', '\n', text)  # Normalize line endings
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_by_slide(self, text: str) -> List[str]:
        """Split presentation text by slides (form feed or special markers)."""
        # Try form feed first
        if '\f' in text:
            slides = text.split('\f')
        # Fallback to slide markers that loaders might insert
        elif '---SLIDE---' in text:
            slides = text.split('---SLIDE---')
        else:
            # If no slide markers, treat as single slide
            slides = [text]
        
        return [s.strip() for s in slides if s.strip()]
    
    def _split_by_email_block(self, text: str) -> List[str]:
        """Split email text removing quoted replies to avoid redundancy."""
        # Remove quoted content to avoid redundancy in RAG systems
        lines = text.split('\n')
        cleaned_lines = []
        in_quote_block = False
        quote_depth = 0
        
        for line in lines:
            # Check if line is quoted (starts with > or multiple >)
            quote_markers = len(line) - len(line.lstrip('>'))
            
            # Detect quote headers like "On ... wrote:"
            is_quote_header = any(pattern.match(line) for pattern in self.EMAIL_REPLY_PATTERNS[1:])
            
            if quote_markers > 0 or is_quote_header:
                # This is quoted content - skip it
                in_quote_block = True
                quote_depth = max(quote_depth, quote_markers)
                continue
            elif in_quote_block and line.strip() == '':
                # Empty line might be part of quote block
                continue
            elif in_quote_block and line.strip():
                # Non-empty, non-quoted line - we're out of the quote block
                in_quote_block = False
                quote_depth = 0
            
            if not in_quote_block:
                cleaned_lines.append(line)
        
        # Join back and split by paragraphs
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Now split the cleaned text into chunks
        # For emails, we might want to preserve some structure markers
        blocks = []
        
        # Split on common email separators
        email_sections = re.split(r'\n\s*[-_=]{3,}\s*\n', cleaned_text)
        
        for section in email_sections:
            # Further split long sections by paragraphs
            paragraphs = re.split(r'\n\s*\n', section)
            blocks.extend([p.strip() for p in paragraphs if p.strip()])
        
        return blocks if blocks else [cleaned_text.strip()] if cleaned_text.strip() else []
    
    def _split_by_sentence(self, text: str) -> List[str]:
        """Split text by sentences (useful for fine-grained chunking)."""
        # Simple sentence splitter - can be replaced with nltk or spacy
        sentence_endings = re.compile(r'([.!?])\s+')
        sentences = sentence_endings.split(text)
        
        # Reconstruct sentences with their ending punctuation
        result = []
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                result.append(sentences[i] + sentences[i + 1])
            else:
                result.append(sentences[i])
        
        return [s.strip() for s in result if s.strip()]
    
    def _split_by_email_thread(self, text: str) -> List[str]:
        """Split email thread preserving only the latest messages and thread metadata."""
        # This strategy extracts each unique message in the thread
        # and adds metadata about who replied to whom
        messages = []
        current_message = []
        current_sender = None
        
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for "On ... wrote:" pattern
            wrote_match = re.match(r'^On\s+(.+?)\s+wrote:\s*$', line, re.IGNORECASE)
            
            if wrote_match:
                # Save current message if exists
                if current_message:
                    msg_text = '\n'.join(current_message).strip()
                    if msg_text:
                        # Add metadata about the thread
                        if current_sender:
                            msg_text = f"[Reply from: {current_sender}]\n{msg_text}"
                        messages.append(msg_text)
                
                # Start tracking new message
                current_message = []
                current_sender = wrote_match.group(1)
                
                # Skip the quoted content that follows
                j = i + 1
                while j < len(lines) and (lines[j].startswith('>') or lines[j].strip() == ''):
                    j += 1
                
                # Jump past quoted content
                i = j
                continue
            
            # Regular line - add to current message if not quoted
            if not line.startswith('>'):
                current_message.append(line)
            
            i += 1
        
        # Don't forget the last message
        if current_message:
            msg_text = '\n'.join(current_message).strip()
            if msg_text:
                if current_sender:
                    msg_text = f"[Reply from: {current_sender}]\n{msg_text}"
                messages.append(msg_text)
        
        # If no thread structure detected, fall back to removing quotes
        if not messages:
            return self._split_by_email_block(text)
        
        return messages
    
    # --------------- Internal Processing --------------- #
    
    def _initial_split(self, text: str, strategy: str) -> List[str]:
        """Apply the specified splitting strategy."""
        if strategy not in self._strategy_registry:
            print(f"Warning: Unknown strategy '{strategy}', falling back to by_paragraph")
            strategy = "by_paragraph"
        
        return self._strategy_registry[strategy](text)
    
    def _enforce_bounds(self, segments: List[str], rule: ChunkRule) -> List[str]:
        """Ensure all segments fall within token bounds."""
        if not segments:
            return []
        
        bounded = []
        buffer = ""
        
        for segment in segments:
            if not segment:
                continue
            
            segment_tokens = self.token_counter(segment)
            
            # Handle oversized segments
            if rule.max_tokens > 0 and segment_tokens > rule.max_tokens:
                # Split large segment
                if buffer:
                    bounded.append(buffer)
                    buffer = ""
                bounded.extend(self._split_large_segment(segment, rule.max_tokens))
                continue
            
            # Try to merge small segments
            if buffer:
                combined = f"{buffer} {segment}"
                combined_tokens = self.token_counter(combined)
                
                if rule.max_tokens == 0 or combined_tokens <= rule.max_tokens:
                    buffer = combined
                else:
                    bounded.append(buffer)
                    buffer = segment
            else:
                buffer = segment
            
            # Check if buffer meets minimum size
            if self.token_counter(buffer) >= rule.min_tokens:
                bounded.append(buffer)
                buffer = ""
        
        # Handle remaining buffer
        if buffer:
            # Try to merge with last chunk if too small
            if bounded and self.token_counter(buffer) < rule.min_tokens:
                last_combined = f"{bounded[-1]} {buffer}"
                if rule.max_tokens == 0 or self.token_counter(last_combined) <= rule.max_tokens:
                    bounded[-1] = last_combined
                else:
                    bounded.append(buffer)
            else:
                bounded.append(buffer)
        
        return bounded
    
    def _split_large_segment(self, segment: str, max_tokens: int) -> List[str]:
        """Split a segment that exceeds max_tokens."""
        words = segment.split()
        chunks = []
        current_chunk = []
        current_count = 0
        
        for word in words:
            # Estimate tokens for the word
            word_tokens = max(1, self.token_counter(word))
            
            if current_count + word_tokens > max_tokens and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_count = word_tokens
            else:
                current_chunk.append(word)
                current_count += word_tokens
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _apply_overlap_and_wrap(self, segments: List[str], meta: dict[str, Any],
                                rule: ChunkRule, doc_id: str) -> List[Chunk]:
        """Apply overlap and create Chunk objects with metadata."""
        chunks = []
        
        for idx, segment in enumerate(segments):
            chunk_text = segment
            overlap_token_count = 0
            
            # Apply overlap from previous chunk
            if rule.overlap > 0 and idx > 0:
                # Extract last N tokens from previous segment
                prev_words = segments[idx - 1].split()
                overlap_words = prev_words[-rule.overlap:] if len(prev_words) >= rule.overlap else prev_words
                
                if overlap_words:
                    candidate = ' '.join(overlap_words) + ' ' + segment
                    candidate_tokens = self.token_counter(candidate)
                    
                    # Only apply if it doesn't exceed max_tokens
                    if rule.max_tokens == 0 or candidate_tokens <= rule.max_tokens:
                        chunk_text = candidate
                        overlap_token_count = len(overlap_words)
            
            # Create chunk with enriched metadata
            chunk_meta = {
                **meta,
                'chunk_index': idx,
                'total_chunks': len(segments),
                'overlap_tokens': overlap_token_count,
                'chunking_strategy': rule.strategy
            }
            
            chunk = Chunk(
                id=uuid.uuid4().hex[:12],  # Slightly longer for better uniqueness
                doc_id=doc_id,
                text=chunk_text,
                meta=chunk_meta,
                chunk_index=idx,
                overlap_tokens=overlap_token_count,
                token_count=self.token_counter(chunk_text)
            )
            
            chunks.append(chunk)
        
        return chunks


# --------------------------------------------------------------------------- #
# Thread-Safe Singleton Factory
# --------------------------------------------------------------------------- #

_CHUNKER_INSTANCE: Optional[BaseChunker] = None
_CHUNKER_LOCK = threading.Lock()


def get_chunker(rules_path: Optional[Path] = None,
                token_counter: Optional[Callable] = None) -> BaseChunker:
    """Get or create the singleton chunker instance (thread-safe)."""
    global _CHUNKER_INSTANCE
    
    if _CHUNKER_INSTANCE is None:
        with _CHUNKER_LOCK:
            # Double-check pattern
            if _CHUNKER_INSTANCE is None:
                _CHUNKER_INSTANCE = BaseChunker(rules_path, token_counter)
    
    return _CHUNKER_INSTANCE


# --------------------------------------------------------------------------- #
# Convenience Functions for RAG Integration
# --------------------------------------------------------------------------- #

def chunk_document(text: str, doc_type: str, doc_id: Optional[str] = None,
                   additional_meta: Optional[dict] = None) -> List[Chunk]:
    """Convenience function to chunk a single document."""
    chunker = get_chunker()
    
    meta = {
        'doc_type': doc_type,
        'doc_id': doc_id or uuid.uuid4().hex,
        **(additional_meta or {})
    }
    
    return chunker.split(text, meta)


def chunk_documents_batch(documents: List[tuple[str, dict[str, Any]]]) -> List[Chunk]:
    """Chunk multiple documents efficiently."""
    chunker = get_chunker()
    all_chunks = []
    
    for text, meta in documents:
        if not isinstance(text, str) or not isinstance(meta, dict):
            print(f"Warning: Skipping invalid document - text type: {type(text)}, meta type: {type(meta)}")
            continue
            
        try:
            chunks = chunker.split(text, meta)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error chunking document {meta.get('doc_id', 'unknown')}: {e}")
            continue
    
    return all_chunks