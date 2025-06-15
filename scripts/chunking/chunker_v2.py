import uuid
from dataclasses import dataclass, field
from typing import Any  # Callable was removed
from scripts.chunking.rules import get_rule, ChunkRule


@dataclass
class Chunk:
    """
    Represents a chunk of text.
    """
    # Fields without defaults must come before fields with defaults
    doc_id: str
    text: str
    meta: dict[str, Any]
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


class BaseChunker:
    """
    Splits text into chunks based on rules.
    """

    def __init__(self):
        # Potentially initialize with global settings or strategies later
        pass

    def split(self, doc_id: str, text_content: str,
              doc_meta: dict[str, Any]) -> list[Chunk]:
        """
        Splits text into chunks based on the document type specified in meta.

        Args:
            doc_id: The ID of the document.
            text_content: The text content to be split. For 'by_slide'
                          strategy, this is expected to be a single
                          slide's or note's text.
            doc_meta: Metadata for the document. Must include 'doc_type'
                      to fetch chunking rules. Can also include
                      slide-specific metadata for 'by_slide' strategy.

        Returns:
            A list of Chunk objects.
        """
        # The 'doc_type' check was removed here as per previous flake8 output,
        # because get_rule handles missing doc_type by trying a 'default' rule.
        # However, the BaseChunker explicitly raised ValueError if doc_type
        # was missing before calling get_rule. This was confirmed by tests.
        # Reinstating the explicit check for clarity and to match test.
        doc_type = doc_meta.get('doc_type')
        if not doc_type:
            raise ValueError(
                "doc_type must be provided in doc_meta "
                "to determine chunking strategy."
            )

        rule: ChunkRule = get_rule(doc_type)
        chunks: list[Chunk] = []

        if rule.split_strategy == "by_slide":
            # For "by_slide", input `text_content` is a pre-split chunk.
            # `doc_meta` is metadata for this specific chunk (e.g., from
            # PptxIngestor, combined with overall document metadata by caller).
            # Wrap it in a Chunk object. token_bounds/overlap from rule
            # might be used elsewhere or for further splitting if implemented.
            # For now, "simple strategy that creates one chunk per slide text".

            # Use doc_meta directly; it contains slide-specific info.
            # Avoid modifying input dict if reused by caller.
            chunk_meta = doc_meta.copy()
            chunks.append(
                Chunk(doc_id=doc_id, text=text_content, meta=chunk_meta)
            )

        # TODO: Implement other splitting strategies based on rule.split_strategy
        # e.g., "split_on_headings", "split_on_blank_lines", etc.
        # These would operate on text_content assuming it's full document text.

        else:
            # For other strategies, a generic text splitting mechanism is needed.
            # This is out of scope for the current task.
            # A simple fallback might be:
            # chunks.append(
            #     Chunk(doc_id=doc_id, text=text_content, meta=doc_meta)
            # )
            # Currently, returns empty list if strategy is not 'by_slide'.
            # This should be addressed when implementing other strategies.
            # Placeholder for unknown/unimplemented strategies:
            # This makes it clear if called with an unexpected strategy.
            pass  # Or raise NotImplementedError for unhandled strategies

        return chunks
