import pathlib
import re
from docx import Document

def load_docx(path: str | pathlib.Path) -> tuple[str, dict]:
    """
    Return (body_text, metadata) for one .docx file.
    Metadata = {"source": str(path), "content_type": "docx"}.

    Text extraction rules:
    - Include all paragraph text in document order.
    - Include text inside tables (row-major order).
    - Ignore images, comments, footnotes, endnotes.
    - Collapse consecutive whitespace to a single space; trim leading/trailing space.
    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    document = Document(path)
    text_parts = []

    for paragraph in document.paragraphs:
        text_parts.append(paragraph.text)

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    text_parts.append(paragraph.text)

    full_text = " ".join(text_parts)
    # Collapse consecutive whitespace and trim
    processed_text = re.sub(r'\s+', ' ', full_text).strip()

    metadata = {"source": str(path), "content_type": "docx"}
    return processed_text, metadata

if __name__ == "__main__":
    # Example usage
    path = r"C:\git projects\RAG-general-purpose\tests\fixtures\docx\Document.docx"
    text, metadata = load_docx(path)
    print("Extracted Text:")
    print(text)
    print("\nMetadata:")
    print(metadata)