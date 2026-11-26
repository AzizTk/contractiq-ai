from datetime import datetime
from uuid import uuid4
from fastapi import FastAPI, File, HTTPException, UploadFile
from .analysis import analyze
from .config import settings
from .extraction import extract_document
from .storage import get_document, init_db, list_documents, save_document

app = FastAPI(title="ContractIQ AI", version="0.1.0",
    description="Evidence-grounded contract review support. Not legal advice.")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "contractiq-api"}


@app.post("/documents/analyze")
async def analyze_upload(file: UploadFile = File(...)):
    filename = file.filename or "uploaded-document"
    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(400, "Only PDF and DOCX files are supported.")
    content = await file.read()
    if len(content) > settings.contractiq_max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.contractiq_max_upload_mb} MB limit.")
    try:
        chunks = extract_document(filename, content)
        result = analyze(filename, chunks)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Analysis failed: {type(exc).__name__}: {exc}") from exc
    doc_id = str(uuid4())
    save_document(doc_id, filename, result)
    return {"id": doc_id, "filename": filename, "created_at": datetime.utcnow().isoformat(),
            "analysis": result.model_dump(mode="json"),
            "source_text": [{"location": c.location, "text": c.text} for c in chunks]}


@app.get("/documents")
def documents():
    return list_documents()


@app.get("/documents/{document_id}")
def document(document_id: str):
    item = get_document(document_id)
    if not item:
        raise HTTPException(404, "Document not found.")
    return item
