import json
from datetime import datetime
from sqlalchemy import create_engine, text
from .config import settings
from .schemas import ContractAnalysis

connect_args = {"check_same_thread": False} if settings.contractiq_database_url.startswith("sqlite") else {}
engine = create_engine(settings.contractiq_database_url, connect_args=connect_args)


def init_db():
    with engine.begin() as conn:
        conn.execute(text("""CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY, filename TEXT NOT NULL, created_at TEXT NOT NULL, analysis_json TEXT NOT NULL
        )"""))


def save_document(doc_id: str, filename: str, analysis: ContractAnalysis):
    with engine.begin() as conn:
        conn.execute(text("""INSERT INTO documents (id, filename, created_at, analysis_json)
            VALUES (:id, :filename, :created_at, :analysis_json)"""),
            {"id": doc_id, "filename": filename, "created_at": datetime.utcnow().isoformat(),
             "analysis_json": analysis.model_dump_json()})


def list_documents():
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, filename, created_at FROM documents ORDER BY created_at DESC")).mappings().all()
    return [dict(row) for row in rows]


def get_document(doc_id: str):
    with engine.begin() as conn:
        row = conn.execute(text("SELECT * FROM documents WHERE id=:id"), {"id": doc_id}).mappings().first()
    if not row:
        return None
    return {"id": row["id"], "filename": row["filename"], "created_at": row["created_at"],
            "analysis": json.loads(row["analysis_json"])}
