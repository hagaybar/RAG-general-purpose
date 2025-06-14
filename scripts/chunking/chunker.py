import uuid
import re # Added for _split_by_email_block
from dataclasses import dataclass, field
from typing import Any
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
        doc_type = doc_meta.get('doc_type')
        if not doc_type:
            raise ValueError(
                "doc_type must be provided in doc_meta "
                "to determine chunking strategy."
            )

        rule: ChunkRule = get_rule(doc_type)
        raw_chunks_text: list[str] = []

        if rule.split_strategy == "by_slide":
            # 'text_content' is already a single chunk for by_slide
            if text_content.strip(): # Ensure not adding empty content
                raw_chunks_text.append(text_content)
        elif rule.split_strategy == "by_paragraph":
            raw_chunks_text = self._split_by_paragraph(text_content)
        elif rule.split_strategy == "by_email_block":
            raw_chunks_text = self._split_by_email_block(text_content)
        else:
            raise NotImplementedError(
                f"Splitting strategy '{rule.split_strategy}' is not implemented."
            )

        # Process raw text chunks based on token rules (min/max tokens, overlap)
        processed_texts = self._process_chunks_with_rules(raw_chunks_text, rule)

        chunks: list[Chunk] = []
        for text_segment in processed_texts:
            # _process_chunks_with_rules should ensure segments are usable.
            # Stripping here is a final safety measure.
            stripped_segment = text_segment.strip()
            if stripped_segment:
                chunk_meta = doc_meta.copy()  # Use a copy for each chunk
                chunks.append(
                    Chunk(doc_id=doc_id, text=stripped_segment, meta=chunk_meta)
                )
        return chunks

    def _count_tokens(self, text: str) -> int:
        """Counts tokens by splitting text by whitespace."""
        return len(text.split())

    def _split_segment_by_max_tokens(self, text: str, max_tokens: int, rule: ChunkRule) -> list[str]:
        """
        Splits a single text segment if it exceeds max_tokens.
        Tries to split at the last space before the token limit.
        """
        output_segments = []
        current_segment = text.strip()

        while self._count_tokens(current_segment) > max_tokens:
            words = current_segment.split()
            # Estimate split point: take max_tokens words
            # This is a simplification; actual token count of words[:max_tokens] might be slightly different
            # if words themselves have internal spaces, but text.split() handles this.
            split_at_word_index = max_tokens

            # Find the actual character index for the split
            # Join the words up to the estimated split point
            first_part_words = words[:split_at_word_index]
            first_part = " ".join(first_part_words)

            # Ensure we are actually making progress
            if not first_part: # Could happen if max_tokens is very small (e.g., 0 or 1)
                 # If no progress, take the whole segment or what's left, to avoid infinite loop
                 # This case should ideally be handled by rule validation (max_tokens > 0)
                if current_segment: output_segments.append(current_segment)
                current_segment = "" # Break loop
                break

            output_segments.append(first_part)
            remaining_words = words[split_at_word_index:]
            current_segment = " ".join(remaining_words).strip()

        if current_segment: # Add any remaining part
            output_segments.append(current_segment)

        return [s.strip() for s in output_segments if s.strip()]


    def _process_chunks_with_rules(self, raw_segments: list[str], rule: ChunkRule) -> list[str]:
        """
        Processes raw text segments to adhere to min_tokens, max_tokens, and overlap rules.
        """
        if not rule.max_tokens and not rule.min_tokens and not rule.overlap:
            return [s.strip() for s in raw_segments if s.strip()] # No rules to apply

        # 1. Split segments that are too long (max_tokens)
        segments_after_max_split = []
        if rule.max_tokens is not None and rule.max_tokens > 0:
            for segment in raw_segments:
                if self._count_tokens(segment) > rule.max_tokens:
                    segments_after_max_split.extend(
                        self._split_segment_by_max_tokens(segment, rule.max_tokens, rule)
                    )
                else:
                    segments_after_max_split.append(segment)
        else:
            segments_after_max_split = list(raw_segments)

        # Filter out empty strings that might have resulted from splitting
        segments_after_max_split = [s.strip() for s in segments_after_max_split if s.strip()]

        # 2. Merge segments that are too short (min_tokens)
        merged_segments = []
        if rule.min_tokens is not None and rule.min_tokens > 0:
            i = 0
            while i < len(segments_after_max_split):
                current_segment = segments_after_max_split[i]
                current_tokens = self._count_tokens(current_segment)

                if current_tokens < rule.min_tokens:
                    # Try to merge with the next segment if possible
                    if (i + 1) < len(segments_after_max_split):
                        next_segment = segments_after_max_split[i+1]
                        merged_text = current_segment + " " + next_segment # Simple space join
                        merged_tokens = self._count_tokens(merged_text)

                        # If merged text is within max_tokens (if specified)
                        if rule.max_tokens is None or merged_tokens <= rule.max_tokens:
                            merged_segments.append(merged_text)
                            i += 1 # Skip next segment as it's now merged
                        # If merged text exceeds max_tokens, split the merged text
                        elif rule.max_tokens is not None and merged_tokens > rule.max_tokens:
                            merged_segments.extend(
                                self._split_segment_by_max_tokens(merged_text, rule.max_tokens, rule)
                            )
                            i += 1 # Skip next segment
                        else: # Cannot merge without exceeding max_tokens, keep current
                            merged_segments.append(current_segment)
                    else: # Last segment and it's too short, keep it
                        merged_segments.append(current_segment)
                else: # Segment is already long enough
                    merged_segments.append(current_segment)
                i += 1
        else:
            merged_segments = list(segments_after_max_split)

        # Filter out empty strings again after merging/splitting
        merged_segments = [s.strip() for s in merged_segments if s.strip()]

        # 3. Apply overlap
        if rule.overlap is not None and rule.overlap > 0 and len(merged_segments) > 0:
            if not merged_segments: # No segments to process (already checked by len(merged_segments) > 0)
                processed_segments = [] # Should be empty list
            else:
                final_chunks_with_overlap = []
                final_chunks_with_overlap.append(merged_segments[0]) # First chunk added as is

                for i in range(1, len(merged_segments)):
                prev_segment_text = merged_segments[i-1]
                current_segment_text = merged_segments[i]

                prev_words = prev_segment_text.split()

                # Ensure overlap does not exceed previous chunk length
                actual_overlap_count = min(rule.overlap, len(prev_words))

                if actual_overlap_count > 0:
                    overlap_words = prev_words[-actual_overlap_count:]
                    overlap_prefix = " ".join(overlap_words)
                    final_chunks_with_overlap.append(overlap_prefix + " " + current_segment_text)
                else: # No possible overlap (e.g. prev_words is empty)
                    final_chunks_with_overlap.append(current_segment_text)
            processed_segments = final_chunks_with_overlap

        else: # No overlap to apply or no segments
            processed_segments = list(merged_segments)

        return [s.strip() for s in processed_segments if s.strip()]


    def _split_by_paragraph(self, text_content: str) -> list[str]:
        """Splits text by double newline characters."""
        paragraphs = text_content.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_by_email_block(self, text_content: str) -> list[str]:
        """
        Splits text by email reply markers (e.g., '^> ', 'On ... wrote:').
        Falls back to paragraph splitting if no markers are found.
        """
        # Regex to find lines starting with common email reply markers
        # This regex looks for lines that START with ">" or "On " and end with "wrote:"
        # It splits *before* these lines.
        pattern = r"^(?:> |On .* wrote:)"

        # Find all split points
        split_points = [match.start() for match in re.finditer(pattern, text_content, re.MULTILINE)]

        if not split_points:
            # No markers found, or text is a single block. Fallback to paragraph splitting.
            return self._split_by_paragraph(text_content)

        segments = []
        current_pos = 0
        for point in split_points:
            if point > current_pos: # Ensure we don't create empty segments at the start
                segments.append(text_content[current_pos:point])
            current_pos = point

        # Add the last segment after the final split point
        if current_pos < len(text_content):
            segments.append(text_content[current_pos:])

        return [s.strip() for s in segments if s.strip()]
