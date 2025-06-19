# Scripts/Chunking Folder

The `scripts/chunking` folder contains Python modules and scripts dedicated to splitting documents into smaller, manageable chunks. This is a crucial step in preparing data for Retrieval Augmented Generation (RAG) systems, as it allows for more focused and efficient processing, embedding, and retrieval of information.

The folder includes different versions or approaches to chunking, primarily distinguished as "v2" and "v3".

## Files

- `__init__.py`: An empty file that marks the `scripts/chunking` directory as a Python package.

- **`models.py`**:
    - Defines a `Chunk` dataclass with the following attributes:
        - `text`: The actual text content of the chunk.
        - `meta`: A dictionary to store metadata associated with the chunk (e.g., source document, page number).
        - `token_count`: The number of tokens in the chunk.
    - This `Chunk` dataclass is primarily utilized by `chunker_v3.py`.

- **`chunker_v2.py`**:
    - Defines an older `Chunk` dataclass (distinct from the one in `models.py`).
    - Implements a `BaseChunker` class responsible for chunking documents.
    - This chunker relies on chunking rules defined and loaded by `rules.py`.
    - It seems to primarily support a "by_slide" chunking strategy, suggesting a focus on presentation-like documents.

- **`rules.py`**:
    - Defines a `ChunkRule` dataclass with attributes such as:
        - `split_strategy`: The method to use for splitting.
        - `token_bounds`: Likely defining target token ranges for chunks.
        - `overlap`: Specifies the amount of overlap between consecutive chunks.
        - `notes`: Additional information or comments about the rule.
        - `min_chunk_size`: The minimum desired size for a chunk.
    - Contains functions to load these chunking rules from the `configs/chunk_rules.yaml` file. This version is associated with `chunker_v2.py`.

- **`chunker_v3.py`**:
    - Implements a core `split` function that orchestrates the chunking process based on rules from `rules_v3.py`.
    - Supports a variety of chunking strategies, including:
        - `"by_paragraph"`
        - `"by_slide"`
        - `"split_on_sheets"` (likely for spreadsheets)
        - `"blank_line"`
        - `"split_on_rows"` (likely for tabular data)
        - `"by_email_block"`
    - Utilizes the `spacy` library for more granular sentence splitting, particularly for email content.
    - Includes logic for merging smaller chunks to meet size requirements and can introduce overlaps between chunks.
    - Uses the `Chunk` dataclass defined in `models.py`.

- **`rules_v3.py`**:
    - Defines a different `ChunkRule` dataclass compared to `rules.py`, with attributes:
        - `strategy`: The chunking strategy to apply.
        - `min_tokens`: The minimum number of tokens a chunk should have.
        - `max_tokens`: The maximum number of tokens a chunk can have.
        - `overlap`: The number of tokens to overlap between adjacent chunks.
    - Provides its own functions to load these rules from the `configs/chunk_rules.yaml` file.
    - Implements stricter validation for the loaded rules compared to `rules.py`. This version is associated with `chunker_v3.py`.

## Versions and Approaches

The presence of `chunker_v2.py`/`rules.py` and `chunker_v3.py`/`rules_v3.py` suggests an evolution in the chunking methodology:
- **v2 (`chunker_v2.py`, `rules.py`)**: Represents an older approach, possibly with a more limited set of strategies and a different rule structure.
- **v3 (`chunker_v3.py`, `rules_v3.py`, `models.py`)**: Represents a newer, more flexible approach with support for diverse strategies, more sophisticated rule definitions (including stricter validation), and specific handling for different content types (e.g., using `spacy` for emails).

It's important to understand which version is being used in different parts of the project, as their behaviors and rule configurations differ.
