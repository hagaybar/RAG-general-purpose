# Embeddings Folder

The `scripts/embeddings` folder is designated for scripts and modules related to generating and managing text embeddings. Text embeddings are numerical representations of text that capture semantic meaning, allowing for tasks like similarity search, which is crucial for Retrieval Augmented Generation (RAG) systems.

- `__init__.py`: An empty file that marks the `embeddings` folder as a Python package.
- `ChunkEmbedder.py`: Contains the `ChunkEmbedder` class, which is central to the embedding generation process.

## ChunkEmbedder

The `ChunkEmbedder` class (`ChunkEmbedder.py`) is responsible for generating embeddings for text chunks and managing their storage in a FAISS index and corresponding metadata. It is utilized by the `embed` command defined in `app/cli.py`.

Key functionalities include:

- **Initialization**:
    - Takes a `ProjectManager` instance (from `scripts.core.project_manager`) to manage project paths and configurations.
    - Initializes a SentenceTransformer model for generating embeddings. The default model is "BAAI/bge-large-en", but this can be configured.

- **Loading Chunks**:
    - `load_chunks_from_tsv()`: Reads chunk data from a TSV file named `chunks.tsv`, expected to be located in the project's `input` directory (as defined by the `ProjectManager`). Each row in the TSV likely represents a chunk and its associated metadata.

- **Running the Embedding Process**:
    - `run(chunks)`: This is the main method that orchestrates the embedding process.
        - It takes a list of `Chunk` objects (presumably from `scripts.chunking.models.Chunk`).
        - It groups these chunks by their `doc_type` (a metadata attribute indicating the source document type, e.g., 'pdf', 'email').
        - For each document type, it calls `_process_doc_type`.

- **Processing by Document Type**:
    - `_process_doc_type(doc_type, chunks)`: This private method handles the embedding and storage for chunks of a specific document type.
        - **FAISS Index Management**:
            - It attempts to read an existing FAISS index for the given `doc_type` from the path provided by `ProjectManager`.
            - If no index exists, it creates a new `IndexFlatL2` FAISS index. FAISS is a library for efficient similarity search.
        - **Metadata Management**:
            - It reads an existing JSONL (JSON Lines) file for metadata associated with the `doc_type`.
            - It extracts existing chunk IDs from this metadata to avoid processing and storing duplicate chunks.
        - **Embedding Generation**:
            - For new chunks (those not found in the existing metadata), it encodes their text content using the initialized SentenceTransformer model to produce numerical embeddings.
        - **Deduplication**:
            - It uses a SHA256 hash of the chunk's text content as a unique identifier (`chunk_id`). This ID is used for deduplication against existing metadata.
        - **Storage**:
            - New embeddings are added to the FAISS index.
            - New metadata (including the `chunk_id` and other relevant details) is appended to the JSONL metadata file.
        - The FAISS index and metadata files are saved to paths determined by the `ProjectManager` (typically within the project's `output/faiss` and `output/metadata` directories, respectively).

- **Logging**:
    - The class utilizes a `LoggerManager` (presumably a custom logging utility from `scripts.utils.logger`) to log information about its operations, such as the number of chunks processed, new chunks added, and paths to saved files.

In summary, `ChunkEmbedder` provides a robust mechanism to convert textual chunks into searchable embeddings, ensuring efficient storage and deduplication, and integrating with the project's defined structure via `ProjectManager`.
