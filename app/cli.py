import pathlib
import typer  # type: ignore
import json  # Added import
import csv  # Added import

from scripts.ingestion.manager import IngestionManager
from scripts.chunking.chunker_v2 import BaseChunker, Chunk  # Added import


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
        chunker = BaseChunker()
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
                # This metadata should include 'doc_type'
                document_chunks = chunker.split(
                    doc_id=doc_id,
                    text_content=raw_doc.content,
                    doc_meta=raw_doc.metadata
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
                    header = ['chunk_id', 'doc_id', 'text', 'meta_json']
                    writer.writerow(header)
                    for chk in all_chunks:
                        meta_json_str = json.dumps(chk.meta)
                        writer.writerow([chk.id, chk.doc_id,
                                         chk.text, meta_json_str])
                print(f"Chunks written to {output_filepath.resolve()}")
            except IOError as e:
                print(f"Error writing chunks to TSV file: {e}")
                raise typer.Exit(code=1)
        else:
            print("No chunks were generated.")


@app.command()
def embed(project_dir: str):
    """
    Embed chunks from project_dir/input/chunks.tsv and store FAISS index and metadata.
    """
    from scripts.core.project_manager import ProjectManager
    from scripts.embeddings import ChunkEmbedder

    project = ProjectManager(project_dir)
    embedder = ChunkEmbedder(project)
    chunks = embedder.load_chunks_from_tsv()
    embedder.run(chunks)



if __name__ == "__main__":
    app()
