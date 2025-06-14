from scripts.chunking.chunker_v3 import split
from scripts.chunking.models import Chunk

def test_split_enforces_max_tokens():
    # This creates 10 paragraphs of 30 tokens each = 300 tokens total
    para = "word " * 30
    doc = "\n\n".join([para] * 10)

    # txt strategy allows only 100 tokens max per chunk
    meta = {"doc_type": "test_txt_small"}


    chunks = split(doc, meta)

    # Should be split into ~3 chunks of max 100 tokens
    assert all(isinstance(c, Chunk) for c in chunks)
    assert len(chunks) >= 3

    for chunk in chunks:
        assert chunk.token_count <= 100, f"Chunk exceeds max_tokens: {chunk.token_count}"
