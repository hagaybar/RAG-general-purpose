# Scripts Folder

The `scripts` folder contains Python scripts that implement the core logic of the project, particularly around document processing for a Retrieval Augmented Generation (RAG) system.

- `__init__.py`: This file is empty and is used to mark the `scripts` folder as a Python package.

The folder is organized into several subdirectories, each responsible for a specific aspect of the processing pipeline:

- **`agents/`**: Likely contains scripts related to AI agents or agentic behavior within the RAG system. (Currently appears to contain only an `__init__.py`)
- **`chunking/`**: Contains modules for splitting documents into smaller, manageable chunks. This includes `chunker.py` for the base chunking logic and `rules.py` for defining chunking rules.
- **`embeddings/`**: Intended for scripts related to generating embeddings for the text chunks. (Currently appears to contain only an `__init__.py`)
- **`index/`**: Likely holds scripts for creating and managing an index of the embeddings, which is used for efficient retrieval. (Currently appears to contain only an `__init__.py`)
- **`ingestion/`**: Contains modules for loading and parsing various document formats. This includes loaders for DOCX (`docx_loader.py`), email (`email_loader.py`), PDF (`pdf.py`), and PowerPoint (`pptx.py`), as well as an `ingestion_manager.py` to orchestrate the ingestion process and `models.py` for data structures related to ingestion.
- **`prompting/`**: Intended for scripts related to constructing prompts for the language model in the RAG system. (Currently appears to contain only an `__init__.py`)
- **`retrieval/`**: Likely contains scripts for retrieving relevant chunks from the index based on a query. (Currently appears to contain only an `__init__.py`)
- **`utils/`**: Contains utility scripts, such as `msg2email.py` for converting MSG files to EML format.

These scripts work together to form a pipeline: documents are ingested, chunked, converted to embeddings, indexed, and then retrieved to augment prompts for a language model. The `app/cli.py` often serves as an interface to these scripts.
