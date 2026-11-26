# ContractIQ AI

Evidence-grounded contract review workspace. Upload PDF/DOCX contracts and extract parties, clauses, obligations, and potential review flags with source excerpts.

> Decision-support only, not legal advice. Findings require qualified human review.

## Quickstart (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn contractiq.api:app --reload
```

In a second terminal:

```powershell
.venv\Scripts\activate
streamlit run dashboard/app.py
```

Dashboard: http://localhost:8501 · API docs: http://localhost:8000/docs

## Features
- PDF, DOCX and TXT extraction with page/paragraph references
- Structured contract snapshot and obligation extraction
- Explainable flags for liability, indemnity, termination, renewal, payment and confidentiality
- Evidence excerpts for findings
- Streamlit dashboard and FastAPI backend
- Optional OpenAI structured analysis; rules-based baseline without an API key
- SQLite persistence and pytest suite

Set OPENAI_API_KEY and optionally OPENAI_MODEL (default gpt-4o-mini) to enable LLM analysis. Without a key, the app explicitly labels its output rules-based.

## API
- GET /health
- POST /documents/analyze
- GET /documents
- GET /documents/{document_id}

Scanned PDFs require OCR, which is not included in this MVP. Do not upload confidential contracts to an untrusted deployment. See samples/sample_contract.txt for a fictional demo agreement.

Author: Aziz Taktak · https://github.com/AzizTk · https://aziz-portfolio-deploy.vercel.app
