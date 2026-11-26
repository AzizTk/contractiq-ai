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
        extract_document("contract.csv", b"hello")
    except ValueError as exc:
        assert "Unsupported file type" in str(exc)
    else:
        raise AssertionError("Expected unsupported file error")


def test_txt_extraction_reads_sample_text():
    chunks = extract_document("sample.txt", b"Provider shall deliver services.")
    assert chunks[0].location == "Text file"
    assert "shall deliver" in chunks[0].text
