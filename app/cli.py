import pathlib
import typer  # type: ignore
import json  # Added import
import csv  # Added import

from scripts.ingestion.manager import IngestionManager
from scripts.chunking.chunker_v3 import split as chunker_split
from scripts.chunking.models import Chunk
from scripts.embeddings.ChunkEmbedder import ChunkEmbedder  # adjust if needed
from scripts.utils.logger import LoggerManager


app = typer.Typer()


@app.command()
def ingest(
    folder_path: pathlib.Path = typer.Argument(
        ..., help="Path to the folder to ingest."
    ),
    chunk: bool = typer.Option(
        False, "--chunk", help="Enable chunking of ingested documents."
    )
):
    """
    Ingests documents from the specified folder and optionally chunks them.
    """
    if not folder_path.is_dir():
        print(f"Error: {folder_path} is not a valid directory.")
        raise typer.Exit(code=1)

    ingestion_manager = IngestionManager()
    raw_docs = ingestion_manager.ingest_path(folder_path)

    # Changed "documents" to "text segments"
    print(f"Ingested {len(raw_docs)} text segments from {folder_path}")

    if chunk:
        if not raw_docs:
            print("No documents were ingested, skipping chunking.")
            raise typer.Exit()

        print("Chunking ingested documents...")
        all_chunks: list[Chunk] = []

        for raw_doc in raw_docs:
            # Ensure doc_id is properly assigned for chunking
            # RawDoc.metadata should contain 'source_filepath'
            doc_id = raw_doc.metadata.get('source_filepath', 'unknown_document')
            if not raw_doc.metadata.get('doc_type'):
                warning_msg = (
                    f"Warning: doc_type missing in metadata for {doc_id}, "
                    f"content: {raw_doc.content[:100]}..."
                )
                print(warning_msg)
                # Potentially skip or assign default doc_type
                # BaseChunker will raise error if doc_type is missing.

            try:
                # Ensure raw_doc.metadata contains 'doc_id' as expected by chunker_v3.py.
                # The 'doc_id' key should ideally be populated by the IngestionManager or here if not.
                # For now, we rely on 'source_filepath' being in metadata and chunker_v3 using meta.get('doc_id').
                # Let's ensure 'doc_id' is explicitly set in the metadata passed to the chunker for clarity.
                current_meta = raw_doc.metadata.copy()
                current_meta['doc_id'] = doc_id # doc_id is from raw_doc.metadata.get('source_filepath', ...)

                document_chunks = chunker_split(
                    text=raw_doc.content,
                    meta=current_meta
                    # clean_options will use default from chunker_v3.split
                )
                all_chunks.extend(document_chunks)
            except ValueError as e:
                error_msg = (
                    f"Skipping chunking for a segment from {doc_id} "
                    f"due to error: {e}"
                )
                print(error_msg)
            except Exception as e:
                error_msg = (
                    f"An unexpected error occurred while chunking a segment "
                    f"from {doc_id}: {e}"
                )
                print(error_msg)

        print(f"Generated {len(all_chunks)} chunks.")

        if all_chunks:
            output_filepath = pathlib.Path("chunks.tsv")
            try:
                with open(output_filepath, "w", newline="",
                          encoding="utf-8") as tsvfile:
                    writer = csv.writer(tsvfile, delimiter='\t')
                    header = ['chunk_id', 'doc_id', 'text', 'token_count', 'meta_json']
                    writer.writerow(header)
                    for chk in all_chunks:
                        meta_json_str = json.dumps(chk.meta)
                        writer.writerow([chk.id, chk.doc_id,
                                         chk.text, chk.token_count, meta_json_str])
                print(f"Chunks written to {output_filepath.resolve()}")
            except IOError as e:
                print(f"Error writing chunks to TSV file: {e}")
                raise typer.Exit(code=1)
        else:
            print("No chunks were generated.")


@app.command()
def embed(
    project_dir: pathlib.Path = typer.Argument(..., help="Path to the project directory")
):
    """
    Embeds chunks.tsv in the given project and saves FAISS index + metadata.
    """
    logger = LoggerManager.get_logger("embedder")

    if not project_dir.is_dir():
        logger.error(f"Provided project_dir does not exist: {project_dir}")
        raise typer.Exit(code=1)

    embedder = ChunkEmbedder(project_dir=project_dir)
    embedder.run()

if __name__ == "__main__":
    app()
