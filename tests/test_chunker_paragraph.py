# tests/test_chunker_paragraph.py
import pytest

# Adjust the import path if your package layout differs
from scripts.chunking.chunker_v3 import split

# A tiny three-paragraph sample (double line-break separates paragraphs)
DOC_TEXT = (
    "First paragraph.\n"
    "\n"
    "Second paragraph.\n"
    "\n"
    "Third paragraph."
)

def test_split_returns_three_paragraph_chunks():
    """split() should return a list with one chunk per paragraph."""
    meta = {"doc_type": "txt", "source": "unit-test"}
    chunks = split(DOC_TEXT, meta)

    # Basic shape checks
    assert isinstance(chunks, list), "split() must return a list"
    assert len(chunks) == 3, "Expected 3 chunks for 3 paragraphs"

    # For the first implementation, treat each chunk as plain text
    for chunk in chunks:
        assert isinstance(chunk, str), "Chunk should be a string for now"
        assert chunk.strip(), "Chunk text should not be empty"
