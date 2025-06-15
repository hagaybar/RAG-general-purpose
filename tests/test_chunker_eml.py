import pytest
from scripts.chunking import chunker_v3
from scripts.chunking.models import Chunk
from scripts.chunking.rules_v3 import get_rule


def count_tokens(text: str) -> int:
    return len(text.split())


def test_chunker_eml_by_email_block():
    # Simulated multi-part email body
    raw_email = """
Hi team,

Just a quick reminder to submit your timesheets by Friday.

Thanks,
Alice

On Mon, Bob wrote:
> Hi Alice,
> Thanks for the update.
> I'll get it done by EOD.

From: carol@example.com
Subject: RE: Timesheets
> Absolutely. I'm syncing with my manager now.
"""

    meta = {
        "doc_type": "eml",
        "content_type": "email",
        "sender": "alice@example.com",
        "subject": "Timesheet Reminder"
    }

    rule = get_rule("eml")
    chunks: list[Chunk] = chunker_v3.split(raw_email, meta)

    # --- Basic structure ---
    assert isinstance(chunks, list)
    assert all(isinstance(c, Chunk) for c in chunks)
    assert len(chunks) >= 2, "Should split reply blocks into multiple chunks"

    # --- Token bounds ---
    for i, c in enumerate(chunks):
        assert c.token_count <= rule.max_tokens + 20
        if i < len(chunks) - 1:
            assert c.token_count >= rule.min_tokens or i == 0  # allow short reply chunks
        assert c.meta["doc_type"] == "eml"

    # --- Overlap logic (optional) ---
    if len(chunks) >= 2 and rule.overlap:
        words1 = chunks[0].text.split()
        words2 = chunks[1].text.split()

        overlap = rule.overlap
        if len(words1) >= overlap and len(words2) >= overlap:
            assert words1[-overlap:] == words2[:overlap], "Overlap mismatch"

