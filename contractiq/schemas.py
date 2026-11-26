from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    location: str
    quote: str


class Finding(BaseModel):
    category: str
    title: str
    severity: Literal["high", "medium", "low", "info"]
    explanation: str
    recommendation: str
    evidence: list[Evidence] = Field(default_factory=list)


class Obligation(BaseModel):
    party: str
    obligation: str
    deadline: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class ContractAnalysis(BaseModel):
    document_name: str
    analysis_mode: Literal["rules-based", "openai"]
    summary: str
    parties: list[str] = Field(default_factory=list)
    effective_date: str | None = None
    end_date: str | None = None
    governing_law: str | None = None
    contract_value: str | None = None
    currency: str | None = None
    clauses_detected: list[str] = Field(default_factory=list)
    obligations: list[Obligation] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
