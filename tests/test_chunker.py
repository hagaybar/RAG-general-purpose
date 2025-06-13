import unittest
from unittest.mock import patch  # MagicMock removed
import uuid

from scripts.chunking.chunker import BaseChunker, Chunk
from scripts.chunking.rules import ChunkRule  # For creating mock return value


class TestBaseChunker(unittest.TestCase):

    def setUp(self):
        self.chunker = BaseChunker()

    @patch('scripts.chunking.chunker.get_rule')
    def test_by_slide_strategy_pptx(self, mock_get_rule):
        # Configure mock for 'pptx'
        mock_pptx_rule = ChunkRule(
            split_strategy='by_slide',
            # Example bounds, not strictly used by 'by_slide'
            token_bounds=[5, 15],
            overlap=0,
            notes='PPTX rule'
        )
        mock_get_rule.return_value = mock_pptx_rule

        doc_id = "test_ppt_doc_001"
        text_content = "This is the text content of a single slide."
        doc_meta = {
            'doc_type': 'pptx',
            'slide_number': 1,
            'source_filepath': 'path/to/doc.pptx'
        }

        chunks = self.chunker.split(doc_id=doc_id,
                                    text_content=text_content,
                                    doc_meta=doc_meta)

        # Assert get_rule was called correctly
        mock_get_rule.assert_called_once_with('pptx')

        self.assertIsNotNone(chunks)
        self.assertEqual(len(chunks), 1)

        chunk = chunks[0]
        self.assertIsInstance(chunk, Chunk)
        self.assertEqual(chunk.doc_id, doc_id)
        self.assertEqual(chunk.text, text_content)
        self.assertEqual(chunk.meta, doc_meta)  # BaseChunker copies doc_meta

        # Check ID properties
        self.assertIsNotNone(chunk.id)
        self.assertIsInstance(chunk.id, str)
        try:
            uuid.UUID(chunk.id, version=4)
        except ValueError:
            self.fail("Chunk ID is not a valid UUID4 hex string")

    @patch('scripts.chunking.chunker.get_rule')
    def test_chunk_id_uniqueness(self, mock_get_rule):
        # Configure a generic rule for these calls
        mock_rule = ChunkRule(split_strategy='by_slide',
                              token_bounds=[10, 20], overlap=0, notes='')
        mock_get_rule.return_value = mock_rule

        doc_meta_1 = {'doc_type': 'pptx', 'slide_number': 1}
        chunks1 = self.chunker.split(doc_id="doc1",
                                     text_content="text for first chunk",
                                     doc_meta=doc_meta_1)

        # Different slide, effectively different "item"
        doc_meta_2 = {'doc_type': 'pptx', 'slide_number': 2}
        chunks2 = self.chunker.split(doc_id="doc1",
                                     text_content="text for second chunk",
                                     doc_meta=doc_meta_2)

        self.assertEqual(len(chunks1), 1)
        self.assertEqual(len(chunks2), 1)

        chunk1 = chunks1[0]
        chunk2 = chunks2[0]

        self.assertNotEqual(chunk1.id, chunk2.id,
                            "Chunk IDs should be unique")

    def test_missing_doc_type_in_meta(self):
        with self.assertRaisesRegex(ValueError,
                                     "doc_type must be provided in doc_meta"):
            self.chunker.split(
                doc_id="test_doc_002",
                text_content="Some text here.",
                doc_meta={'slide_number': 1}  # Missing 'doc_type'
            )

    @patch('scripts.chunking.chunker.get_rule')
    def test_get_rule_raises_key_error(self, mock_get_rule):
        # Configure get_rule to simulate failure for an unknown doc_type.
        # This occurs if 'unknown_type' isn't in rules.yaml and no default
        # is configured in get_rule.
        error_msg = "No rule found for doc_type 'unknown_type'"
        mock_get_rule.side_effect = KeyError(error_msg)

        doc_meta = {'doc_type': 'unknown_type'}
        with self.assertRaisesRegex(KeyError, error_msg):
            self.chunker.split(
                doc_id="test_doc_003",
                text_content="Content for an unknown type.",
                doc_meta=doc_meta
            )
        mock_get_rule.assert_called_once_with('unknown_type')

    @patch('scripts.chunking.chunker.get_rule')
    def test_other_strategy_returns_empty_list(self, mock_get_rule):
        # Test current behavior for an unimplemented strategy
        mock_other_rule = ChunkRule(
            split_strategy='by_heading',  # Assume this is not 'by_slide'
            token_bounds=[100, 500],
            overlap=0,
            notes='Other rule'
        )
        mock_get_rule.return_value = mock_other_rule

        doc_meta = {'doc_type': 'docx'}
        chunks = self.chunker.split(
            doc_id="test_doc_004",
            text_content="Full document content for docx.",
            doc_meta=doc_meta
        )

        # BaseChunker currently only implements 'by_slide'.
        # Other strategies result in no chunks. This test verifies that.
        # It might need adjustment if/when other strategies are added.
        self.assertEqual(
            len(chunks), 0,
            "Expected empty list for unimplemented strategies other than 'by_slide'"
        )
        mock_get_rule.assert_called_once_with('docx')


if __name__ == "__main__":
    unittest.main()
