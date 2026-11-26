from dataclasses import dataclass
from io import BytesIO
from docx import Document
import fitz


@dataclass
class TextChunk:
    location: str
    text: str


def extract_document(filename: str, content: bytes) -> list[TextChunk]:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    chunks: list[TextChunk] = []
    if suffix == "pdf":
        with fitz.open(stream=content, filetype="pdf") as pdf:
            for page_no, page in enumerate(pdf, start=1):
                value = page.get_text("text").strip()
                if value:
                    chunks.append(TextChunk(location=f"Page {page_no}", text=value))
    elif suffix == "docx":
        doc = Document(BytesIO(content))
        for idx, paragraph in enumerate(doc.paragraphs, start=1):
            value = paragraph.text.strip()
            if value:
                chunks.append(TextChunk(location=f"Paragraph {idx}", text=value))
        for table_idx, table in enumerate(doc.tables, start=1):
            for row_idx, row in enumerate(table.rows, start=1):
                value = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if value:
                    chunks.append(TextChunk(location=f"Table {table_idx}, row {row_idx}", text=value))
    else:
        raise ValueError("Unsupported file type. Upload a PDF or DOCX document.")
    if not chunks:
        raise ValueError("No extractable text found. This may be a scanned PDF; OCR is not included yet.")
    return chunks
