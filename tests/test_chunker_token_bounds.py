from scripts.chunking.chunker_v3 import split
from scripts.chunking.models import Chunk

def test_split_enforces_max_tokens():
    para = "word " * 30    # 30 tokens per paragraph
    doc = "\n\n".join([para] * 10)  # 10 x 30 = 300 tokens
    meta = {"doc_type": "test_txt_small"}

    chunks = split(doc, meta)

    for i, c in enumerate(chunks):
        print(f"Chunk {i}: {c.token_count} tokens")

    # If no merging, we get 10 chunks of 30
    # If merging works, we should get fewer chunks of ~90–100 tokens
    assert len(chunks) < 10, "Chunks were not merged as expected"
    assert all(c.token_count <= 100 for c in chunks)
    assert all(c.token_count >= 30 for c in chunks)
