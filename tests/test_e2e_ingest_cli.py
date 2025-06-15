# tests/test_e2e_ingest_cli.py
from pathlib import Path
from typer.testing import CliRunner

import pytest
pytestmark = pytest.mark.legacy_chunker


import sys
import os
import shutil
# Go up one level from tests to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.cli import app            # <- the Typer app defined in app/cli.py
from scripts.ingestion.manager import IngestionManager

runner = CliRunner()

def test_ingest_cli_end_to_end(tmp_path):
    # 1. Prepare a scratch copy of the fixture bundle
    fixture_dir = Path("tests/fixtures/e2e_ingest")   # eml + docx + pdf
    work_dir = tmp_path / "dataset"

    # IngestionManager.copy_tree(fixture_dir, work_dir)  # or shutil.copytree
    shutil.copytree(fixture_dir, work_dir)

    # 2. Invoke: rag ingest <folder>
    result = runner.invoke(app, [str(work_dir)])

    # 3. Assertions
    assert result.exit_code == 0, result.stdout
    assert "Ingested 3" in result.stdout
