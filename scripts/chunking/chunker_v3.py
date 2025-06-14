# scripts/chunking/chunker_v3.py
"""
Chunker v3 – first slice: paragraph strategy.

For this initial step we:
1. Keep the public signature split(text, meta) -> list
2. Implement a *very* simple paragraph splitter: blank-line separates paragraphs
3. Return a plain list[str] so existing tests pass
"""

import re
from typing import Any, Dict, List
from .models import Chunk

from scripts.chunking.rules_v3 import get_rule


PARA_REGEX = re.compile(r"\n\s*\n")  # one or more blank lines



# --- helpers -----------------------------------------------------------------
def _token_count(text: str) -> int:
    """Very rough token counter; will be replaced by real tokenizer later."""
    return len(text.split())


# --- public API --------------------------------------------------------------
def split(text: str, meta: dict) -> list[Chunk]:
    rule = get_rule(meta["doc_type"])

    # 1. Split into raw paragraphs
    paragraphs = [
        p.strip() for p in PARA_REGEX.split(text.strip()) if p.strip()
    ]

    # 2. Merge into chunks within token bounds
    chunks = []
    buffer = []
    buffer_tokens = 0

    for para in paragraphs:
        para_tokens = _token_count(para)

        # If adding this would exceed max, flush current buffer
        if buffer and buffer_tokens + para_tokens > rule.max_tokens:
            chunk_text = "\n\n".join(buffer)
            if buffer_tokens >= rule.min_tokens:
                chunks.append(Chunk(
                    text=chunk_text,
                    meta=meta.copy(),
                    token_count=buffer_tokens,
                ))
            buffer = []
            buffer_tokens = 0

        # Add this para
        buffer.append(para)
        buffer_tokens += para_tokens

    # Flush remainder
    if buffer:
        chunk_text = "\n\n".join(buffer)
        chunks.append(Chunk(
            text=chunk_text,
            meta=meta.copy(),
            token_count=buffer_tokens,
        ))

    return chunks
