# Ingestion Folder

The `scripts/ingestion` folder is responsible for loading and parsing documents from various file formats. This is the first step in the data processing pipeline for the RAG system, preparing raw content for subsequent chunking, embedding, and indexing.

This folder contains:

- `__init__.py`: This file likely initializes a `LOADER_REGISTRY` (though its definition isn't shown here, it's used by `manager.py`). This registry maps file extensions (e.g., ".pdf", ".docx") to their corresponding loader functions or classes.

- `models.py`: Defines the data structures and base classes for the ingestion process.
    - **`RawDoc` dataclass**: Represents a single piece of raw content extracted from a file before it's chunked. It contains:
        - `content: str`: The textual content.
        - `metadata: dict`: A dictionary of metadata about the content (e.g., source file, document type).
    - **`AbstractIngestor` (ABC)**: An abstract base class for creating ingestor classes. It defines an `ingest()` method that concrete ingestors must implement. This is useful for loaders that might produce multiple `RawDoc` instances from a single file (e.g., `PptxIngestor`).
    - **`UnsupportedFileError` exception**: A custom exception raised when a file cannot be processed (e.g., corrupted, encrypted, or unsupported format).

- `manager.py`: Contains the `IngestionManager` class, which orchestrates the ingestion process.
    - **`IngestionManager` class**:
        - Its `ingest_path(path: str | pathlib.Path) -> List[RawDoc]` method takes a file or directory path.
        - It recursively searches for files (`rglob("*")`) within the given path.
        - For each file, it checks its suffix against the `LOADER_REGISTRY`.
        - If a loader is found, it invokes it. It handles both function-based loaders and class-based ingestors (subclasses of `AbstractIngestor`).
        - For class-based ingestors (like `PptxIngestor`), it instantiates the class and calls its `ingest()` method, which can return multiple text segments (each becoming a `RawDoc`).
        - For function-based loaders, it calls the function, expecting `(content, metadata)` to be returned, which is then wrapped in a `RawDoc`.
        - It populates `base_metadata` with `source_filepath` and `doc_type` and merges it with metadata returned by the loader/ingestor.
        - It collects all `RawDoc` objects and returns them as a list.
        - Includes error handling for `UnsupportedFileError` and other exceptions during loading.

- `docx_loader.py`:
    - **`load_docx(path: str | pathlib.Path) -> tuple[str, dict]`**:
        - Parses Microsoft Word (`.docx`) files using the `python-docx` library.
        - Extracts text from paragraphs and tables (in row-major order).
        - Ignores images, comments, footnotes, and endnotes.
        - Collapses consecutive whitespace and trims the result.
        - Returns the extracted text and a metadata dictionary: `{"source": str(path), "content_type": "docx"}`.

- `email_loader.py`:
    - **`load_eml(path: str | Path) -> tuple[str, dict]`**:
        - Parses email (`.eml`) files using Python's built-in `email` module.
        - Prioritizes extracting the `text/plain` part of the email. If not found, it gets the body content.
        - Returns the extracted plain text and a metadata dictionary: `{"source": str(path), "content_type": "email"}`.

- `pdf.py`:
    - **`load_pdf(path: str | Path) -> RawDoc`**: (Note: The signature in `manager.py` implies it expects `(content, metadata)` from function loaders, while this is typed to return `RawDoc`. Assuming it's adapted or the `manager.py` handles it).
        - Parses PDF (`.pdf`) files using the `pdfplumber` library.
        - Extracts text from each page and joins them with double newlines.
        - Raises `UnsupportedFileError` if the PDF is encrypted, corrupted, has no pages, or contains no extractable text.
        - Returns the extracted text and a metadata dictionary containing `source_path`, `title`, `author`, `created`, `modified`, and `num_pages`.
        - Handles various PDF-related exceptions (`PDFPasswordIncorrect`, `PDFSyntaxError`, `PdfminerException`).

- `pptx.py`:
    - **`PptxIngestor(AbstractIngestor)` class**:
        - Implements the `ingest(self, filepath: str) -> list[tuple[str, dict]]` method for PowerPoint (`.pptx`) files using the `python-pptx` library.
        - Extracts text from shapes on each slide and from presenter notes.
        - For each slide, it can produce two separate text segments: one for the slide content and one for the presenter notes if available.
        - Returns a list of tuples, where each tuple is `(text_segment, metadata)`. The metadata includes `slide_number`, `type` ("slide_content" or "presenter_notes"), and `doc_type` ("pptx").
        - Raises `UnsupportedFileError` if the file is not a `.pptx` file or if errors occur during processing.

**Integration:**
The `IngestionManager` is the primary entry point for ingesting documents. It uses the various specialized loaders and ingestors registered in `LOADER_REGISTRY` to handle different file types. The output (`List[RawDoc]`) from the ingestion process is then typically passed to the chunking components (`scripts/chunking/`) for further processing.
