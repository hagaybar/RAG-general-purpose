from .csv import load_csv
from .docx_loader import load_docx
from .email_loader import load_eml
from .pdf import load_pdf  # Add this import
from .pptx import PptxIngestor  # Import PptxIngestor

LOADER_REGISTRY = {
    ".csv": load_csv,
    ".docx": load_docx,
    ".eml": load_eml,
    ".pdf": load_pdf,  # Add this mapping
    ".pptx": PptxIngestor,  # Map .pptx to PptxIngestor class
}
