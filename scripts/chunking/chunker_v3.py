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
def split(text: str, meta: Dict[str, Any]) -> List[Chunk]:
    """Split document into Chunk objects, one per paragraph."""
    raw_paras = [
        p.strip()
        for p in PARA_REGEX.split(text.strip())
        if p.strip()
    ]

    return [
        Chunk(text=p,
              meta=meta.copy(),
              token_count=_token_count(p))
        for p in raw_paras
    ]
