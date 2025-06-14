"""Unified tests for BaseChunker / chunker utilities
====================================================
This single file merges the functional pytest suite we wrote earlier with key
checks from the original `unittest` draft provided by the user.  It is designed
so that **either** project layout will work:

* `scripts.chunking.chunker` (package‑style, used by the CLI)
* `chunker` at repo root (stand‑alone module)

The tests favour *pytest* because the rest of the repo already uses it (see
`tests/` folder and Poetry dev‑dependencies).  Where the original `unittest`
file relied on `unittest.mock.patch`, we instead inject rules directly into the
`BaseChunker` instance for speed and simplicity.

Run with:
    poetry run pytest -vv tests/test_chunker.py
"""

from __future__ import annotations

import importlib
import inspect
from typing import List, Any

import pytest

# --------------------------------------------------------------------------- #
# Dynamic import – support both layouts
# --------------------------------------------------------------------------- #

try:
    chunker_mod = importlib.import_module("scripts.chunking.chunker")
except ModuleNotFoundError:
    chunker_mod = importlib.import_module("chunker")

BaseChunker = chunker_mod.BaseChunker
Chunk = chunker_mod.Chunk
ChunkRule = getattr(chunker_mod, "ChunkRule", None)  # May be internal only
get_chunker = getattr(chunker_mod, "get_chunker", None)
chunk_document = getattr(chunker_mod, "chunk_document", None)
chunk_documents_batch = getattr(chunker_mod, "chunk_documents_batch", None)

# --------------------------------------------------------------------------- #
# Helpers & fixtures
# --------------------------------------------------------------------------- #


def _make_words(n: int, word: str = "lorem") -> str:
    """Return a space‑separated string with *n* copies of *word*."""
    return " ".join([word] * n)


@pytest.fixture()
def fresh_chunker():
    """Reload the chunker module each time to reset the singleton & rules."""
    importlib.reload(chunker_mod)
    return BaseChunker()


def _call_split(chunker: BaseChunker, text: str, meta: dict[str, Any]):
    """Call `split` using whichever signature this version of chunker exposes."""
    sig = inspect.signature(chunker.split)
    params = list(sig.parameters)
    if len(params) == 3:  # old signature: (doc_id, text_content, doc_meta)
        return chunker.split(doc_id=meta.get("doc_id", "doc1"),
                              text_content=text,
                              doc_meta=meta)
    # new signature: (text, meta)
    return chunker.split(text, meta)


# --------------------------------------------------------------------------- #
# Tests merged from BOTH suites
# --------------------------------------------------------------------------- #


def test_by_slide_strategy_pptx(fresh_chunker):
    """`by_slide` rule should return exactly one chunk for single‑slide text."""
    chunker = fresh_chunker

    if ChunkRule is None:
        pytest.skip("ChunkRule type not exposed in this build")

    # Inject a mock rule so we don't rely on YAML
    chunker._rules["pptx"] = ChunkRule(strategy="by_slide",
                                        min_tokens=1,
                                        max_tokens=0,
                                        overlap=0)

    text_content = "This is the text content of a single slide."
    meta = {"doc_type": "pptx", "slide_number": 1}

    chunks = _call_split(chunker, text_content, meta)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.text == text_content
    assert chunk.meta["doc_type"] == "pptx"


def test_chunk_id_uniqueness(fresh_chunker):
    """Chunk IDs generated for separate splits must be distinct UUID‑likes."""
    chunker = fresh_chunker

    if ChunkRule is None:
        pytest.skip("ChunkRule type not exposed in this build")

    chunker._rules["pptx"] = ChunkRule(strategy="by_slide", min_tokens=1,
                                        max_tokens=0, overlap=0)
    meta1 = {"doc_type": "pptx", "slide_number": 1}
    meta2 = {"doc_type": "pptx", "slide_number": 2}

    c1 = _call_split(chunker, "Slide one", meta1)[0]
    c2 = _call_split(chunker, "Slide two", meta2)[0]

    assert c1.id != c2.id


def test_default_rule_when_missing_doc_type(fresh_chunker):
    """If `doc_type` is absent, the chunker should fall back to its default rule."""
    chunker = fresh_chunker
    chunks = _call_split(chunker, "Some plain text", {})

    assert len(chunks) >= 1
    assert chunks[0].meta["chunking_strategy"] == chunker._default_rule.strategy


def test_paragraph_splitting_and_overlap(fresh_chunker):
    """Two paragraphs over min_tokens should yield two chunks with overlap."""
    chunker = fresh_chunker

    paragraph = _make_words(60)
    text = f"{paragraph}\n\n{paragraph}"
    meta = {"doc_type": "txt"}

    chunks = _call_split(chunker, text, meta)

    assert len(chunks) == 2
    assert chunks[1].overlap_tokens == chunker._default_rule.overlap


def test_batch_skip_invalid_input():
    """`chunk_documents_batch` must ignore non‑string/non‑dict entries."""
    if chunk_documents_batch is None:
        pytest.skip("Batch helper not available in this build")

    docs = [
        ("valid " * 10, {"doc_type": "txt"}),
        (42, {}),  # invalid – should be skipped
    ]

    chunks = chunk_documents_batch(docs)
    assert len(chunks) == 1
