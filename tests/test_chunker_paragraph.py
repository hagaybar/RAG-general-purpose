# tests/test_chunker_paragraph.py
from scripts.chunking.chunker_v3 import split
from scripts.chunking.models import Chunk

DOC_TEXT = (
    "First paragraph.\n\n"
    "Second paragraph.\n\n"
    "Third paragraph."
)

def test_split_returns_three_chunk_objects():
    chunks = split(DOC_TEXT, {"doc_type": "txt"})
    assert len(chunks) == 1
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(p in chunks[0].text for p in ["First paragraph.", "Second paragraph.", "Third paragraph."])
