# Chunking Folder

The `scripts/chunking` folder is responsible for the logic of splitting documents into smaller, more manageable pieces called chunks. This is a crucial step in preparing data for many NLP tasks, especially for Retrieval Augmented Generation (RAG) systems, as it helps in creating focused context for embeddings and retrieval.

This folder contains:

- `__init__.py`: An empty file that marks `scripts/chunking` as a Python package.

- `chunker.py`: This module defines the core chunking classes and logic.
    - **`Chunk` dataclass**: Represents a single chunk of text. It includes:
        - `doc_id`: The identifier of the original document.
        - `text`: The actual text content of the chunk.
        - `meta`: A dictionary for storing metadata associated with the chunk (e.g., source, page number, slide number).
        - `id`: A unique identifier for the chunk, generated by default using `uuid.uuid4()`.
    - **`BaseChunker` class**: This class provides the main functionality for splitting text.
        - Its `split()` method takes a document ID, text content, and document metadata (which must include `doc_type`) as input.
        - It retrieves the appropriate chunking rule for the given `doc_type` using `get_rule` from `rules.py`.
        - Currently, it explicitly implements the `"by_slide"` splitting strategy, where the input `text_content` is assumed to be pre-split (e.g., text from a single PowerPoint slide), and it wraps this content into a `Chunk` object.
        - Other splitting strategies (e.g., "split_on_headings", "split_on_blank_lines") are intended to be implemented here. The `split()` method will need to be extended to handle these, operating on the full document text for those strategies. If a `doc_type` is missing in the metadata, it raises a `ValueError`.

- `rules.py`: This module handles the loading and management of chunking rules, which are defined externally in `configs/chunk_rules.yaml`.
    - **`ChunkRule` dataclass**: Represents the chunking parameters for a specific document type. It includes:
        - `split_strategy`: The name of the strategy to use (e.g., "by_slide", "split_on_headings").
        - `token_bounds`: Optional list defining target token counts (e.g., `[min_tokens, max_tokens]`).
        - `overlap`: Optional integer specifying the token overlap between adjacent chunks.
        - `notes`: Optional descriptive notes about the rule.
        - `min_chunk_size`: Optional; kept for compatibility, but `token_bounds` is preferred.
    - **`_load_rules_if_needed()`**: A private function that loads the chunking rules from `configs/chunk_rules.yaml` into a global `_rules_data` variable if they haven't been loaded already. It includes fallback logic to find the YAML file.
    - **`get_rule(doc_type: str) -> ChunkRule`**: Retrieves the `ChunkRule` for a given `doc_type`. If the specific `doc_type` is not found, it attempts to fall back to a "default" rule. It raises a `KeyError` if neither is found and `FileNotFoundError` if the rules YAML cannot be located.
    - **`get_all_rules() -> dict[str, ChunkRule]`**: Returns a dictionary of all defined chunking rules, mapping document types to their `ChunkRule` objects.
    - **`get_all_doc_types() -> list[str]`**: Returns a list of all document types for which rules are defined.

**Integration:**
The `chunker.py` module is used by other parts of the system (e.g., `app/cli.py` during the ingestion process) to break down raw ingested documents. The `rules.py` module provides the necessary configuration to the chunker, making the chunking process adaptable to different file types based on the settings in `configs/chunk_rules.yaml`.
