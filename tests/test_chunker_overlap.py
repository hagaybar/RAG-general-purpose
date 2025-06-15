from scripts.chunking.chunker_v3 import split
from scripts.chunking.models import Chunk
from scripts.chunking.rules_v3 import ChunkRule
from scripts.chunking import rules_v3



def test_split_debug_import():
    print(f">>> split() is from: {split.__module__}")


def test_overlap_tokens_are_preserved(monkeypatch):
    # Force rule: max 60 tokens per chunk, overlap 5

    monkeypatch.setattr(
        "scripts.chunking.chunker_v3.get_rule",
        lambda doc_type: ChunkRule(
            strategy="blank_line",
            min_tokens=10,
            max_tokens=60,
            overlap=5
        )
    )


    # 6 paragraphs of 20 tokens = 120 tokens total
    para = "word " * 20
    doc = "\n\n".join([para] * 6)
    meta = {"doc_type": "txt"}

    chunks = split(doc, meta)
    print(f"Got {len(chunks)} chunks")
    for i, c in enumerate(chunks):
        print(f"Chunk {i}: {c.token_count} tokens")


    assert len(chunks) >= 2

    tokens_0 = chunks[0].text.split()
    tokens_1 = chunks[1].text.split()

    # Overlap: last 5 tokens of chunk 0 == first 5 tokens of chunk 1
    assert tokens_0[-5:] == tokens_1[:5], "Overlap tokens were not preserved"
