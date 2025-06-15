import unittest
from unittest.mock import patch
from scripts.chunking.chunker_v2 import BaseChunker, Chunk
from scripts.chunking.rules import ChunkRule, get_rule # Ensure get_rule can be patched if needed, or rules are directly constructed
import pytest

pytestmark = pytest.mark.legacy_chunker

# Helper function to count tokens (consistent with chunker's method)
def count_tokens(text: str) -> int:
    return len(text.split())

class TestChunkerDocxPdf(unittest.TestCase):

    def setUp(self):
        self.chunker = BaseChunker()
        # Sample text with paragraph breaks and roughly estimable token count.
        # Let's aim for a text that can be split into a few paragraphs.
        # Each 'Lorem ipsum...' block is ~30 words.
        # 5 blocks = ~150 words. We need more for 800 tokens. Let's use a placeholder.
        # For actual testing, a more controlled text is better.
        # This text has 4 paragraphs.
        self.lorem_ipsum_text = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " # P1, S1
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. " # P1, S2
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.\n\n" # P1, S3 (ends paragraph)
            "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. " # P2, S1
            "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.\n\n" # P2, S2 (ends paragraph)
            "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, " # P3, S1
            "eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.\n\n" # P3, S2 (ends paragraph)
            "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. " # P4, S1
            "Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit." # P4, S2
        )
        # Simplified text for easier token counting and overlap verification
        self.simple_text_docx = "Para1 word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24 word25 word26 word27 word28 word29 word30 word31 word32 word33 word34 word35 word36 word37 word38 word39 word40 word41 word42 word43 word44 word45 word46 word47 word48 word49 word50 word51 word52 word53 word54 word55.\n\nPara2 word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24 word25 word26 word27 word28 word29 word30 word31 word32 word33 word34 word35 word36 word37 word38 word39 word40." # 55 + 40 = 95 tokens
        self.simple_text_pdf = "PDFPara1 word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24 word25 word26 word27 word28 word29 word30 word31 word32 word33 word34 word35 word36 word37 word38 word39 word40 word41 word42 word43 word44 word45 word46 word47 word48 word49 word50.\n\nPDFPara2 word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24 word25." # 50 + 25 = 75 tokens

        # DOCX rule: by_paragraph, min_tokens: 50, max_tokens: 300, overlap: 20
        self.docx_rule = ChunkRule(
            split_strategy='by_paragraph',
            min_tokens=50,
            max_tokens=300,
            overlap=20,
            notes="Test DOCX rule"
        )
        # PDF rule: by_paragraph, min_tokens: 50, max_tokens: 300, overlap: 20
        self.pdf_rule = ChunkRule(
            split_strategy='by_paragraph',
            min_tokens=50,
            max_tokens=300,
            overlap=20,
            notes="Test PDF rule"
        )
        # Rule for testing merging
        self.merge_test_rule_docx = ChunkRule(
            split_strategy='by_paragraph',
            min_tokens=30, # Para1 (20) is less, Para2 (15) is less
            max_tokens=100,
            overlap=5,
            notes="Test DOCX rule for merging"
        )
    @patch("scripts.chunking.rules.get_rule")
    def test_docx_by_paragraph_strategy(self, mock_get_rule):
        mock_get_rule.return_value = self.docx_rule
        doc_meta = {'doc_type': 'docx'}
        doc_id = "test_docx_doc"

        # Using simple_text_docx: Para1 (55 tokens), Para2 (40 tokens)
        # Expected: Para1 (55 tokens) is > min_tokens (50). Para2 (40 tokens) is < min_tokens (50), so it will merge with Para1.
        # Merged chunk: Para1 + Para2 = 55 + 40 = 95 tokens.
        # This merged chunk is within [50, 300]. So, 1 chunk expected.
        # If Para2 was > 50, then 2 chunks. Let's adjust simple_text_docx or rule for a 2-chunk scenario first.

        # Test 1: Both paragraphs are large enough
        text_two_large_paras = "Para1 " + "word " * 55 + "\n\n" + "Para2 " + "word " * 60 # 56 + 61 tokens
        chunks = self.chunker.split(text_two_large_paras, doc_meta)
        # mock_get_rule.assert_called_once_with('docx')
        self.assertEqual(len(chunks), 2)
        self.assertTrue(count_tokens(chunks[0].text) >= self.docx_rule.min_tokens)
        self.assertTrue(count_tokens(chunks[0].text) <= self.docx_rule.max_tokens)
        self.assertTrue(count_tokens(chunks[1].text) >= self.docx_rule.min_tokens) # Second chunk also respects min_tokens

        # Verify overlap for the second chunk
        if len(chunks) > 1 and self.docx_rule.overlap > 0:
            prev_chunk_tokens = chunks[0].text.split()
            current_chunk_tokens = chunks[1].text.split()
            # Ensure overlap does not exceed previous chunk length
            actual_overlap_count = min(self.docx_rule.overlap, len(prev_chunk_tokens))
            overlap_tokens = prev_chunk_tokens[-actual_overlap_count:]
            self.assertEqual(current_chunk_tokens[:actual_overlap_count], overlap_tokens)

    @patch("scripts.chunking.rules.get_rule")
    def test_pdf_by_paragraph_strategy_with_merge(self, mock_get_rule):
        # PDF rule: by_paragraph, min_tokens: 50, max_tokens: 300, overlap: 20
        # This test will use a specific rule for PDF to test merging.
        pdf_merge_rule = ChunkRule(split_strategy='by_paragraph', min_tokens=40, max_tokens=100, overlap=5)
        mock_get_rule.return_value = pdf_merge_rule
        doc_meta = {'doc_type': 'pdf'}
        doc_id = "test_pdf_doc_merge"

        # Test merging: Para1 (small), Para2 (small enough to merge without exceeding max)
        # SmallPara1 has 21 tokens ("SmallPara1 " + "word " * 20)
        # SmallPara2 has 16 tokens ("SmallPara2 " + "word " * 15)
        text_for_merge = "SmallPara1 " + "word " * 20 + "\n\n" + "SmallPara2 " + "word " * 15
        # Rule: min_tokens=40.
        # P1 (21 tokens) is < 40. P2 (16 tokens).
        # Expected: P1 merges with P2. Merged text = P1 + " " + P2.
        # Token count of merged: 21 + 16 = 37 tokens.
        # This merged chunk (37 tokens) is < min_tokens (40).
        # According to logic: "If it's the last segment and it's too short, it's kept as is."
        # The merge logic: if current is short, try to merge with next. If merged is still too short, it's kept.
        # If merged is too long, it's split. If merged is just right, it's kept.

        chunks = self.chunker.split(text_for_merge, doc_meta)
        # mock_get_rule.assert_called_once_with('pdf')

        self.assertEqual(len(chunks), 1) # Expect P1 and P2 to merge
        merged_chunk_token_count = count_tokens(chunks[0].text)

        # The merged chunk (37 tokens) is less than min_tokens (40).
        # It should be kept as one merged chunk because P2 was the last segment to merge with P1.
        self.assertEqual(merged_chunk_token_count, 21 + 16) # 37 words
        self.assertTrue(merged_chunk_token_count < pdf_merge_rule.min_tokens) # Confirms it's below min_tokens
        self.assertTrue(merged_chunk_token_count < pdf_merge_rule.max_tokens)


    @patch("scripts.chunking.rules.get_rule")
    def test_docx_long_paragraph_split_and_overlap(self, mock_get_rule):
        # Rule: min 50, max 60, overlap 10
        docx_split_rule = ChunkRule(split_strategy='by_paragraph', min_tokens=50, max_tokens=60, overlap=10)
        mock_get_rule.return_value = docx_split_rule
        doc_meta = {'doc_type': 'docx'}
        doc_id = "test_docx_split_overlap"

        # A single long paragraph of 100 words.
        long_para_text = "Word " * 100
        # Expected processing:
        # 1. Raw segments: ["Word " * 100] (after paragraph splitting, it's one segment)
        # 2. Max_tokens split (max=60):
        #    - First part: "Word " * 60
        #    - Remainder: "Word " * 40
        #    Segments after max split: ["Word "*60, "Word "*40]
        # 3. Min_tokens merge (min=50):
        #    - Segment 1 ("Word "*60): Count=60. OK (>=50). Added to merged_segments.
        #    - Segment 2 ("Word "*40): Count=40. Too short (<50). It's the last segment. Kept as is.
        #    Segments after merge: ["Word "*60, "Word "*40]
        # 4. Overlap (overlap=10):
        #    - Chunk 1 final: "Word "*60 (first chunk, no change from overlap perspective)
        #    - Chunk 2 original: "Word "*40. Previous chunk original: "Word "*60.
        #    - Overlap text from previous: last 10 words of ("Word "*60).
        #    - Chunk 2 final: ("Word "*10) + " " + ("Word "*40) = "Word "*50 (actually 10 unique words + space + 40 unique words)
        #      The count will be 10 (overlap words) + 40 (original words) = 50 words.

        chunks = self.chunker.split(long_para_text,doc_meta)
        # mock_get_rule.assert_called_once_with('docx')

        self.assertEqual(len(chunks), 2)

        c1_tokens = count_tokens(chunks[0].text)
        c2_tokens = count_tokens(chunks[1].text)

        self.assertEqual(c1_tokens, 60) # First chunk should be at max_tokens

        # Second chunk: original 40 tokens + 10 overlap tokens from first chunk
        # Expected text: "Word Word ... (10 times from overlap) Word Word ... (40 times original)"
        self.assertEqual(c2_tokens, 40 + docx_split_rule.overlap) # 50 tokens

        self.assertTrue(c1_tokens >= docx_split_rule.min_tokens)
        self.assertTrue(c2_tokens >= docx_split_rule.min_tokens) # 50 >= 50, this is correct

        # Verify overlap content
        chunk0_words = chunks[0].text.split()
        chunk1_words = chunks[1].text.split()

        # Ensure overlap does not exceed previous chunk length
        actual_overlap_count = min(docx_split_rule.overlap, len(chunk0_words))
        expected_overlap_words = chunk0_words[-actual_overlap_count:]
        self.assertEqual(chunk1_words[:actual_overlap_count], expected_overlap_words)

    # TODO: Add a test for the 800-token lorem ipsum text if feasible to construct and verify.
    # For now, the focused tests above cover strategy, merging, splitting, and overlap.

if __name__ == '__main__':
    unittest.main()
