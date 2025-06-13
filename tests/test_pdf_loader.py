import pytest
from pathlib import Path
from scripts.ingestion.pdf import load_pdf
from scripts.ingestion.models import RawDoc, UnsupportedFileError
# If pdfplumber is needed for test setup (e.g. creating test PDFs), it should be imported as 'import pdfplumber'

# Define fixture paths (adjust if your fixture directory is different)
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "pdf"
SIMPLE_PDF = FIXTURES_DIR / "simple.pdf"
ENCRYPTED_PDF = FIXTURES_DIR / "encrypted.pdf"
NO_TEXT_PDF = FIXTURES_DIR / "no_text.pdf"

# Helper to create a simple PDF for testing (if not providing actual files)
# For a more robust solution, you would typically add pre-made fixture files to your repo
# For this subtask, we will try to create them if they don't exist.
def _create_test_pdfs_if_not_exist():
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    if not SIMPLE_PDF.exists():
        try:
            import pdfplumber
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(str(SIMPLE_PDF))
            c.setTitle("Simple Test PDF")
            c.setAuthor("Test Author")
            # Page 1
            c.drawString(100, 750, "This is page 1.")
            c.showPage()
            # Page 2
            c.drawString(100, 750, "This is page 2.")
            c.showPage()
            c.save()
        except ImportError:
            print("ReportLab is not installed. Skipping creation of simple.pdf. Please create it manually.")
            # Fallback: create an empty file so the path exists
            SIMPLE_PDF.touch()


    if not ENCRYPTED_PDF.exists():
        try:
            import pdfplumber
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(str(ENCRYPTED_PDF))
            c.drawString(100, 750, "This is an encrypted document.")
            # Standard encryption with user password "password"
            c.setEncrypt("password")
            c.showPage()
            c.save()
        except ImportError:
            print("ReportLab is not installed. Skipping creation of encrypted.pdf. Please create it manually.")
            ENCRYPTED_PDF.touch()

    if not NO_TEXT_PDF.exists():
        try:
            import pdfplumber
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(str(NO_TEXT_PDF))
            # Add an image or just save an empty page to simulate no text
            c.showPage() # Empty page
            c.save()
        except ImportError:
            print("ReportLab is not installed. Skipping creation of no_text.pdf. Please create it manually.")
            NO_TEXT_PDF.touch()

_create_test_pdfs_if_not_exist()


class TestPDFLoader:
    def test_load_simple_pdf_success(self):
        # This test assumes simple.pdf was created successfully by the helper or exists
        if not SIMPLE_PDF.exists() or SIMPLE_PDF.stat().st_size == 0:
             pytest.skip("simple.pdf fixture not available for testing.")

        doc = load_pdf(SIMPLE_PDF)
        assert isinstance(doc, RawDoc)
        assert doc.content == "This is page 1.\n\nThis is page 2."
        assert doc.metadata["source_path"] == str(SIMPLE_PDF.resolve())
        assert doc.metadata["title"] == "Simple Test PDF"
        assert doc.metadata["author"] == "Test Author"
        assert doc.metadata["num_pages"] == 2
        # Created and modified dates are harder to assert precisely without knowing the test environment
        # So, we'll just check if they exist for now, or are None if pdfplumber couldn't get them.
        assert "created" in doc.metadata
        assert "modified" in doc.metadata

    def test_load_encrypted_pdf_raises_error(self):
        if not ENCRYPTED_PDF.exists() or ENCRYPTED_PDF.stat().st_size == 0:
            pytest.skip("encrypted.pdf fixture not available for testing.")

        with pytest.raises(UnsupportedFileError, match="is encrypted and requires a password"):
            load_pdf(ENCRYPTED_PDF)

    def test_load_no_text_pdf_raises_error(self):
        # This test assumes no_text.pdf was created or exists
        if not NO_TEXT_PDF.exists() or NO_TEXT_PDF.stat().st_size == 0:
             pytest.skip("no_text.pdf fixture not available for testing.")

        with pytest.raises(UnsupportedFileError, match="No extractable text found"):
            load_pdf(NO_TEXT_PDF)

    def test_load_non_existent_pdf_raises_error(self):
        with pytest.raises(FileNotFoundError): # pdfplumber.open raises FileNotFoundError
            load_pdf(Path("non_existent_file.pdf"))

    def test_load_corrupted_pdf_raises_error(self):
        # Create a dummy corrupted file
        corrupted_pdf_path = FIXTURES_DIR / "corrupted.pdf"
        with open(corrupted_pdf_path, "w") as f:
            f.write("This is not a PDF content.")

        with pytest.raises(UnsupportedFileError, match="Failed to parse PDF"):
            load_pdf(corrupted_pdf_path)

        corrupted_pdf_path.unlink() # Clean up
