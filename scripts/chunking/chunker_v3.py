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

    paragraphs = [
        p.strip() for p in PARA_REGEX.split(text.strip()) if p.strip()
    ]

    chunks = []
    buffer = []
    buffer_tokens = 0
    prev_tail_tokens: list[str] = []

    for para in paragraphs:
        para_tokens = _token_count(para)

        if buffer and buffer_tokens + para_tokens > rule.max_tokens:
            # ---- FLUSH current chunk with overlap from previous ----
            chunk_tokens = " ".join(prev_tail_tokens + buffer).split()
            chunk_text = " ".join(chunk_tokens)
            if len(chunk_tokens) >= rule.min_tokens:
                chunks.append(Chunk(
                    text=chunk_text,
                    meta=meta.copy(),
                    token_count=len(chunk_tokens),
                ))

            # Update overlap tail
            prev_tail_tokens = chunk_tokens[-rule.overlap:] if rule.overlap else []

            # Reset
            buffer = []
            buffer_tokens = 0

        buffer.append(para)
        buffer_tokens += para_tokens

    # ---- Flush remainder ----
    if buffer:
        chunk_tokens = " ".join(prev_tail_tokens + buffer).split()
        chunk_text = " ".join(chunk_tokens)
        chunks.append(Chunk(
            text=chunk_text,
            meta=meta.copy(),
            token_count=len(chunk_tokens),
        ))

    return chunks

