import inspect
from typing import get_origin, List

import pytest

from scripts.chunking.chunker_v3 import split


def test_split_signature():
    """Public API must stay (text: str, meta: dict) -> iterable."""
    sig = inspect.signature(split)
    params = list(sig.parameters.values())
    assert [p.name for p in params] == ["text", "meta"], "Keep the two-arg interface"

    # Accept  → list | List[...] | Sequence[...] | no annotation
    origin = get_origin(sig.return_annotation) or sig.return_annotation
    assert origin in (list, inspect._empty), "Return should be list-like"


def test_split_runtime_shape():
    """split() should return a non-empty list for simple input."""
    text = "A.\n\nB."
    chunks = split(text, {"doc_type": "txt"})
    assert isinstance(chunks, list)
    assert chunks == ["A.", "B."]      # strict for now
