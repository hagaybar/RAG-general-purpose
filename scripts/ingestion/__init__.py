from .docx_loader import load_docx
from .email_loader import load_eml

LOADER_REGISTRY = {
    ".docx": load_docx,
    ".eml": load_eml,
}
