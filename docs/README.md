# Docs Folder

The `docs` folder contains documentation files for the project.

- `chunk_rules.md`: This file provides a detailed explanation of the chunking strategies used for different document types. It outlines:
    - Rules by document type (e.g., email, docx, pdf), including split strategy, minimum chunk size, and specific notes.
    - Definitions for various split strategies (e.g., `split_on_blank_lines`, `split_on_headings`).
    - Guidelines for including headers and footers.
    - Special processing notes for certain file types.
    - Considerations for chunk sizes.
    This document is a reference for understanding how content is segmented before further processing in the RAG system.

- `ingest.md`: This file describes the available data loaders for ingesting content into the system. It currently details:
    - Email (`.eml`) loader: Explains how `.eml` files are processed, the function used (`scripts.ingestion.email_loader.load_eml`), what it returns (text content and metadata), and provides a usage example.
    - DOCX (`.docx`) loader: Explains how `.docx` files are processed, the function used (`scripts.ingestion.docx_loader.load_docx`), what it returns (text content and metadata), how it handles various elements like tables and whitespace, and provides a usage example.
    This document serves as a guide for developers on how to use the ingestion scripts and what to expect from them.

The `docs` folder is essential for project maintainability and onboarding new developers, providing clear explanations of key components and processes.
