import unittest
from unittest.mock import patch
from scripts.chunking.chunker import BaseChunker, Chunk
from scripts.chunking.rules import ChunkRule

# Helper function to count tokens (consistent with chunker's method)
def count_tokens(text: str) -> int:
    return len(text.split())

class TestChunkerEml(unittest.TestCase):

    def setUp(self):
        self.chunker = BaseChunker()
        # EML rule: by_email_block, min_tokens: 30, max_tokens: 250, overlap: 10
        self.eml_rule = ChunkRule(
            split_strategy='by_email_block',
            min_tokens=30,
            max_tokens=250,
            overlap=10,
            notes="Test EML rule"
        )
        self.eml_rule_low_min = ChunkRule( # For testing individual blocks
            split_strategy='by_email_block',
            min_tokens=5,
            max_tokens=250,
            overlap=2,
            notes="Test EML rule with low min_tokens"
        )

        self.sample_eml_reply_chain = (
            "This is the latest reply.\n"
            "It has a few lines of text.\n"
            "Hopefully enough tokens for a chunk.\n\n" # approx 19 tokens
            "> This is the first level of quote.\n"
            "> It also has some text.\n"
            "> Enough for a small chunk.\n\n" # approx 17 tokens
            "> > This is a nested quote.\n"
            "> > More deeply nested text here.\n\n" # approx 11 tokens
            "On Some Date, Someone Wrote:\n" # This should also be a split point
            "This is the original message body.\n"
            "It forms the last part of the email." # approx 14 tokens
        )
        # Expected splits based on markers:
        # 1. "This is the latest reply..." (19 tokens)
        # 2. "This is the first level of quote..." (17 tokens, after stripping '>')
        # 3. "This is a nested quote..." (11 tokens, after stripping '>>')
        # 4. "This is the original message body..." (14 tokens)

        self.plain_eml_text_paragraphs = (
            "This is a plain email message.\n"
            "It has no reply markers.\n"
            "Just a few paragraphs of text.\n\n" # approx 19 tokens
            "This is the second paragraph.\n"
            "It should be treated as such by the fallback mechanism." # approx 14 tokens
        )

    @patch("scripts.chunking.rules.get_rule")
    def test_eml_by_email_block_strategy(self, mock_get_rule):
        mock_get_rule.return_value = self.eml_rule_low_min # min_tokens=5 to keep initial blocks separate
        doc_meta = {'doc_type': 'eml'}
        doc_id = "test_eml_doc_blocks"

        chunks = self.chunker.split(doc_id=doc_id, text_content=self.sample_eml_reply_chain, doc_meta=doc_meta)
        mock_get_rule.assert_called_once_with('eml')

        self.assertEqual(len(chunks), 4, "Expected 4 chunks from the reply chain")

        # Check that chunks do not start with "> " after stripping (unless it's the only content)
        # The chunker's strategy implementation should handle stripping the markers themselves.
        # The text content of the chunk should be the block *after* the marker.

        # Chunk 1: "This is the latest reply..."
        self.assertFalse(chunks[0].text.startswith(">"))
        self.assertIn("This is the latest reply.", chunks[0].text)
        self.assertTrue(count_tokens(chunks[0].text) >= self.eml_rule_low_min.min_tokens if self.eml_rule_low_min.min_tokens else True)

        # Chunk 2: "This is the first level of quote..."
        self.assertFalse(chunks[1].text.startswith(">"))
        self.assertIn("This is the first level of quote.", chunks[1].text)
        self.assertTrue(count_tokens(chunks[1].text) >= self.eml_rule_low_min.min_tokens if self.eml_rule_low_min.min_tokens else True)

        # Chunk 3: "This is a nested quote..."
        self.assertFalse(chunks[2].text.startswith(">"))
        self.assertIn("This is a nested quote.", chunks[2].text)
        self.assertTrue(count_tokens(chunks[2].text) >= self.eml_rule_low_min.min_tokens if self.eml_rule_low_min.min_tokens else True)

        # Chunk 4: "This is the original message body..."
        self.assertFalse(chunks[3].text.startswith(">")) # Also checks for "On ... wrote:"
        self.assertFalse(chunks[3].text.lower().startswith("on ")) # More specific check
        self.assertIn("This is the original message body.", chunks[3].text)
        self.assertTrue(count_tokens(chunks[3].text) >= self.eml_rule_low_min.min_tokens if self.eml_rule_low_min.min_tokens else True)

        # Test overlap if applicable (more than 1 chunk)
        if len(chunks) > 1 and self.eml_rule_low_min.overlap > 0:
            for i in range(1, len(chunks)):
                prev_chunk_tokens = chunks[i-1].text.split()
                current_chunk_tokens = chunks[i].text.split()

                # Determine actual overlap words from previous chunk
                actual_overlap_count = min(self.eml_rule_low_min.overlap, len(prev_chunk_tokens))
                expected_overlap_words = prev_chunk_tokens[-actual_overlap_count:]

                # Check if current chunk starts with these words
                self.assertEqual(current_chunk_tokens[:actual_overlap_count], expected_overlap_words,
                                 f"Overlap mismatch between chunk {i-1} and chunk {i}")

    @patch("scripts.chunking.rules.get_rule")
    def test_eml_fallback_to_by_paragraph(self, mock_get_rule):
        mock_get_rule.return_value = self.eml_rule # min_tokens=30
        doc_meta = {'doc_type': 'eml'}
        doc_id = "test_eml_doc_fallback"

        # plain_eml_text_paragraphs: P1 (19 tokens), P2 (14 tokens)
        # Rule: min_tokens=30.
        # Expected: P1 (19) is short. P2 (14) is short.
        # P1 merges with P2 -> 19 + 14 = 33 tokens. This is >= min_tokens (30).
        # So, 1 chunk expected.
        chunks = self.chunker.split(doc_id=doc_id, text_content=self.plain_eml_text_paragraphs, doc_meta=doc_meta)
        mock_get_rule.assert_called_once_with('eml')

        self.assertEqual(len(chunks), 1)
        self.assertFalse(chunks[0].text.startswith(">"))
        # Check if the content reflects merged paragraphs
        self.assertIn("This is a plain email message.", chunks[0].text)
        self.assertIn("This is the second paragraph.", chunks[0].text)

        token_cnt = count_tokens(chunks[0].text)
        self.assertTrue(token_cnt >= self.eml_rule.min_tokens if self.eml_rule.min_tokens else True)
        self.assertTrue(token_cnt <= self.eml_rule.max_tokens if self.eml_rule.max_tokens else True)
        self.assertEqual(token_cnt, 19 + 14) # 33 tokens

    @patch("scripts.chunking.rules.get_rule")
    def test_eml_merging_and_token_limits(self, mock_get_rule):
        # Use self.eml_rule: min_tokens=30, max_tokens=250, overlap=10
        mock_get_rule.return_value = self.eml_rule
        doc_meta = {'doc_type': 'eml'}
        doc_id = "test_eml_merging"

        # Text: Block1 (19), Block2 (17), Block3 (11), Block4 (14)
        # All are < min_tokens (30)
        # Expected merging:
        # 1. B1 (19) is short. Merges B2 (17). B1' = 19+17 = 36. (>=30, <250). Chunks: [B1'(36), B3(11), B4(14)]
        # 2. B3 (11) is short. Merges B4 (14). B3' = 11+14 = 25. (<30). Chunks: [B1'(36), B3'(25)]
        # 3. B3' (25) is short. It's the last processed chunk from merging pass. Kept as is.
        # Resulting texts (before overlap): [text_of_B1', text_of_B3']
        # Apply overlap (10 tokens):
        #   Chunk1_final: text_of_B1' (36 tokens)
        #   Chunk2_final: (last 10 from B1') + text_of_B3' (10 + 25 = 35 tokens)

        chunks = self.chunker.split(doc_id=doc_id, text_content=self.sample_eml_reply_chain, doc_meta=doc_meta)

        self.assertEqual(len(chunks), 2)

        # Original text segments after initial split by strategy (stripping markers):
        # T1: "This is the latest reply..." (19 words)
        # T2: "This is the first level of quote..." (17 words)
        # T3: "This is a nested quote..." (11 words)
        # T4: "This is the original message body..." (14 words)

        # Chunk 1 text (B1' = T1 + T2)
        # Note: The _split_by_email_block method should strip markers and leading/trailing whitespace from segments.
        # The text content of T1 is "This is the latest reply.\nIt has a few lines of text.\nHopefully enough tokens for a chunk."
        # The text content of T2 is "This is the first level of quote.\nIt also has some text.\nEnough for a small chunk."
        # When merged: T1 + " " + T2

        # Check content of chunk 0 (merged T1 and T2)
        self.assertIn("This is the latest reply.", chunks[0].text)
        self.assertIn("Enough for a small chunk.", chunks[0].text) # From T2
        self.assertFalse(chunks[0].text.startswith(">"))

        c1_tokens = count_tokens(chunks[0].text)
        self.assertEqual(c1_tokens, 19 + 17) # 36 tokens
        self.assertTrue(c1_tokens >= self.eml_rule.min_tokens)
        self.assertTrue(c1_tokens <= self.eml_rule.max_tokens)

        # Chunk 2 text (Overlap from C1 + B3' (T3+T4))
        # B3' = T3 + T4 = 11 + 14 = 25 tokens
        # Overlap is 10 tokens from C1 (36 tokens)
        # Content of T3: "This is a nested quote.\nMore deeply nested text here."
        # Content of T4: "This is the original message body.\nIt forms the last part of the email."
        self.assertIn("This is a nested quote.", chunks[1].text) # From T3
        self.assertIn("It forms the last part of the email.", chunks[1].text) # From T4
        self.assertFalse(chunks[1].text.startswith(">"))

        c2_tokens = count_tokens(chunks[1].text)
        self.assertEqual(c2_tokens, (11 + 14) + self.eml_rule.overlap) # 25 + 10 = 35 tokens
        self.assertTrue(c2_tokens >= self.eml_rule.min_tokens)
        self.assertTrue(c2_tokens <= self.eml_rule.max_tokens)

        # Verify overlap content
        chunk0_words = chunks[0].text.split() # This is T1 + " " + T2
        chunk1_words = chunks[1].text.split() # This is Overlap + " " + T3 + " " + T4

        actual_overlap_count = min(self.eml_rule.overlap, len(chunk0_words))
        expected_overlap_words = chunk0_words[-actual_overlap_count:]
        self.assertEqual(chunk1_words[:actual_overlap_count], expected_overlap_words)


if __name__ == '__main__':
    unittest.main()
