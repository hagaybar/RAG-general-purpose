# App Folder

The `app` folder contains the command-line interface (CLI) for the project.

Specifically, it contains:
- `__init__.py`: This file is empty and is used to mark the `app` folder as a Python package.
- `cli.py`: This file defines the CLI commands for the project. It uses the `typer` library to create a simple and user-friendly CLI.
    - The `ingest` command is used to ingest documents from a specified folder. It takes a folder path as an argument and an optional `--chunk` flag to enable chunking of ingested documents.
    - The `embed` command is used to embed chunks from `project_dir/input/chunks.tsv` and store FAISS index and metadata. It takes a project directory path as an argument.
    - The ingested documents are processed by the `IngestionManager` from `scripts.ingestion.manager`.
    - If chunking is enabled, the `BaseChunker` from `scripts.chunking.chunker_v2.BaseChunker` is used to split the documents into smaller chunks.
    - The generated chunks are then written to a TSV file named `chunks.tsv`.

The `app` folder is integrated into the project by providing a user-friendly way to interact with the project's core functionalities, such as document ingestion and chunking.
