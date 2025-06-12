from .docx_loader import load_docx
from .email_loader import load_eml
from .pdf import load_pdf # Add this import

LOADER_REGISTRY = {
    ".docx": load_docx,
    ".eml": load_eml,
    ".pdf": load_pdf, # Add this mapping
}
