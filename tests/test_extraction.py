from io import BytesIO
from docx import Document
from contractiq.extraction import extract_document


def test_docx_extraction_reads_paragraphs():
    doc = Document()
    doc.add_paragraph("Customer shall pay the invoice within 30 days.")
    buffer = BytesIO()
    doc.save(buffer)
    chunks = extract_document("contract.docx", buffer.getvalue())
    assert chunks[0].location == "Paragraph 1"
    assert "30 days" in chunks[0].text


def test_unsupported_file_is_rejected():
    try:
        extract_document("contract.txt", b"hello")
    except ValueError as exc:
        assert "PDF and DOCX" in str(exc)
    else:
        raise AssertionError("Expected unsupported file error")
