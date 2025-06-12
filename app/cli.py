import pathlib
import typer

from scripts.ingestion.manager import IngestionManager

app = typer.Typer()

@app.command()
def ingest(folder_path: pathlib.Path = typer.Argument(..., help="Path to the folder to ingest.")):
    """
    Ingests documents from the specified folder.
    """
    if not folder_path.is_dir():
        print(f"Error: {folder_path} is not a valid directory.")
        raise typer.Exit(code=1)

    ingestion_manager = IngestionManager()
    raw_docs = ingestion_manager.ingest_path(folder_path)

    print(f"Ingested {len(raw_docs)} documents from {folder_path}")

if __name__ == "__main__":
    app()
