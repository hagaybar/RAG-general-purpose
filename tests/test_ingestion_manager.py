import pathlib
import pytest

import sys
import os


# Go up one level from tests to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from scripts.ingestion.manager import IngestionManager
from scripts.ingestion.models import RawDoc

pytestmark = pytest.mark.legacy_chunker

# Define the fixture path relative to this test file
FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures" / "ingestion_test_data"

def test_ingest_path_success():
    manager = IngestionManager()
    docs = manager.ingest_path(FIXTURE_DIR)

    assert len(docs) == 2

    eml_doc_found = False
    docx_doc_found = False

    for doc in docs:
        assert isinstance(doc, RawDoc)
        if doc.metadata["source"].endswith("test_email.eml"):
            eml_doc_found = True
            assert "This is the body of the test email." in doc.content
            assert doc.metadata["content_type"] == "email"
        elif doc.metadata["source"].endswith("test_document.docx"):
            docx_doc_found = True
            assert "This is a test document." in doc.content
            assert doc.metadata["content_type"] == "docx"

    assert eml_doc_found, "Test email file not found or processed."
    assert docx_doc_found, "Test docx file not found or processed."

def test_ingest_path_empty_folder():
    manager = IngestionManager()
    # Create an empty directory for this test
    empty_dir = FIXTURE_DIR / "empty_test_dir"
    empty_dir.mkdir(exist_ok=True)

    docs = manager.ingest_path(empty_dir)
    assert len(docs) == 0

    # Clean up the empty directory
    empty_dir.rmdir()

def test_ingest_path_non_existent_folder():
    manager = IngestionManager()
    non_existent_dir = FIXTURE_DIR / "non_existent_dir"
    docs = manager.ingest_path(non_existent_dir)
    assert len(docs) == 0

def test_ingest_path_with_other_files():
    manager = IngestionManager()
    # Create a directory with a mix of files
    mixed_dir = FIXTURE_DIR / "mixed_test_dir"
    mixed_dir.mkdir(exist_ok=True)

    # Create a .txt file which should be ignored
    with open(mixed_dir / "ignored_file.txt", "w") as f:
        f.write("This file should be ignored.")

    # Copy one of the relevant files into this directory
    test_eml_path = FIXTURE_DIR / "test_email.eml"
    # Ensure the source file exists before copying
    if test_eml_path.exists():
        (mixed_dir / "test_email.eml").write_bytes(test_eml_path.read_bytes())
        docs = manager.ingest_path(mixed_dir)
        assert len(docs) == 1
        assert docs[0].metadata["source"].endswith("test_email.eml")
    else:
        # If the source .eml file doesn't exist (e.g. due to test setup issues),
        # this part of the test cannot run as intended.
        # We can either fail the test or skip this assertion.
        # For now, let's make it explicit if the file is missing.
        pytest.fail(f"Source file for copy operation not found: {test_eml_path}")

    # Clean up the mixed directory and its contents
    for item in mixed_dir.iterdir():
        item.unlink()
    mixed_dir.rmdir()
