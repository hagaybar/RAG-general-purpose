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

PARA_REGEX = re.compile(r"\n\s*\n")  # one or more blank lines

def split(text: str, meta: Dict[str, Any]) -> List[str]:
    """Split document into paragraph chunks (MVP).

    Args:
        text: Raw document text
        meta: Loader-supplied metadata (currently unused)

    Returns:
        List of paragraph strings (whitespace-stripped, empty paras removed)
    """
    paragraphs = [
        p.strip()
        for p in PARA_REGEX.split(text.strip())
        if p.strip()  # drop empty chunks
    ]
    return paragraphs
