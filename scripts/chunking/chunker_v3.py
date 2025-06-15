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
from scripts.chunking.models import Chunk
from scripts.chunking.rules_v3 import ChunkRule
from scripts.chunking.rules_v3 import get_rule


PARA_REGEX = re.compile(r"\n\s*\n")  # one or more blank lines



# --- helpers -----------------------------------------------------------------
def _token_count(text: str) -> int:
    """Very rough token counter; will be replaced by real tokenizer later."""
    return len(text.split())


# --- public API --------------------------------------------------------------

def merge_chunks_with_overlap(paragraphs: list[str], meta: dict, rule: ChunkRule) -> list[Chunk]:
    chunks = []
    buffer = []
    buffer_tokens = 0
    prev_tail_tokens: list[str] = []

    for para in paragraphs:
        para_tokens = _token_count(para)
        print(f"[MERGE] buffer_tokens: {buffer_tokens}, next_para: {para_tokens}")
        print(f"[RULE] max_tokens: {rule.max_tokens}")
        if buffer_tokens + para_tokens >= rule.max_tokens:
            chunk_tokens = " ".join(prev_tail_tokens + buffer).split()
            chunk_text = " ".join(chunk_tokens)
            if len(chunk_tokens) >= rule.min_tokens:
                chunks.append(Chunk(
                    text=chunk_text,
                    meta=meta.copy(),
                    token_count=len(chunk_tokens),
                ))

            prev_tail_tokens = chunk_tokens[-rule.overlap:] if rule.overlap else []
            buffer = []
            buffer_tokens = 0

        buffer.append(para)
        buffer_tokens += para_tokens

    if buffer:
        chunk_tokens = " ".join(prev_tail_tokens + buffer).split()
        chunk_text = " ".join(chunk_tokens)
        chunks.append(Chunk(
            text=chunk_text,
            meta=meta.copy(),
            token_count=len(chunk_tokens),
        ))

    return chunks




def split(text: str, meta: dict) -> list[Chunk]:
    rule = get_rule(meta["doc_type"])

    if rule.strategy in ("by_paragraph", "paragraph"):
        items = [p.strip() for p in PARA_REGEX.split(text.strip()) if p.strip()]
    elif rule.strategy in ("by_slide", "slide"):
        items = [s.strip() for s in text.strip().split("\n---\n") if s.strip()]
    elif rule.strategy in ("split_on_sheets", "sheet", "sheets"):
        items = [text.strip()] if text.strip() else []
    elif rule.strategy in ("blank_line",):
        items = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    elif rule.strategy == "split_on_rows":
        # Each line in the text is a row from the CSV
        items = [row.strip() for row in text.strip().split('\n') if row.strip()]
    else:
        raise ValueError(f"Unsupported strategy: {rule.strategy}")

    return merge_chunks_with_overlap(items, meta, rule)


