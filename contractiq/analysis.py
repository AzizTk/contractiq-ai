import json
import re
from datetime import datetime
from openai import OpenAI
from .config import settings
from .extraction import TextChunk
from .schemas import ContractAnalysis, Evidence, Finding, Obligation

RULES = [
    ("liability", "Liability cap may be absent", "high", r"unlimited liability|without limitation|no limitation of liability", "Review whether liability is capped and whether exclusions are mutual."),
    ("indemnity", "Broad indemnity language", "medium", r"indemnif(?:y|ies|ication).{0,100}(?:all claims|any and all|any loss)", "Check scope, causation, exclusions, and whether the obligation is mutual."),
    ("termination", "Unilateral termination right", "medium", r"(?:sole discretion|at any time).{0,100}terminat|terminat.{0,100}(?:sole discretion|without cause)", "Review notice periods, symmetry, and consequences of termination."),
    ("renewal", "Automatic renewal provision", "medium", r"automatically renew|automatic renewal|successive renewal", "Confirm renewal duration, notice window, and reminder ownership."),
    ("payment", "Late payment terms detected", "info", r"late fee|interest at|overdue amount|past due", "Validate rate, trigger date, grace period, and applicable law."),
    ("confidentiality", "Confidentiality clause detected", "info", r"confidential information|non-disclosure|confidentiality", "Check permitted disclosures, duration, and return or deletion duties."),
]


def _evidence(chunks: list[TextChunk], pattern: str) -> list[Evidence]:
    rx = re.compile(pattern, re.I)
    for chunk in chunks:
        match = rx.search(chunk.text)
        if match:
            start, end = max(0, match.start() - 100), min(len(chunk.text), match.end() + 160)
            quote = " ".join(chunk.text[start:end].split())
            return [Evidence(location=chunk.location, quote=quote)]
    return []


def rules_analysis(filename: str, chunks: list[TextChunk]) -> ContractAnalysis:
    full = "\\n".join(c.text for c in chunks)
    findings = []
    detected = []
    for category, title, severity, pattern, recommendation in RULES:
        if re.search(pattern, full, re.I):
            detected.append(category)
            findings.append(Finding(category=category, title=title, severity=severity,
                explanation="Matching language was found in the extracted document. This is a review prompt, not a legal conclusion.",
                recommendation=recommendation, evidence=_evidence(chunks, pattern)))
    if not re.search(r"governing law|laws of|jurisdiction", full, re.I):
        findings.append(Finding(category="governing law", title="Governing law not detected",
            severity="low", explanation="No common governing-law phrase was detected by the baseline parser.",
            recommendation="Confirm the agreement identifies governing law and dispute forum."))
    parties = []
    for match in re.finditer(r"(?:between|by and between)\\s+([^,;\\n]{3,80})", full, re.I):
        parties.append(match.group(1).strip())
        if len(parties) == 2:
            break
    amounts = re.findall(r"(?:USD|EUR|GBP|\\$|€|£)\\s?\\d[\\d,]*(?:\\.\\d{2})?", full)
    obligations = []
    obligation_pattern = re.compile(r"((?:shall|must|agrees to|is responsible for)\\s+[^.;\\n]{8,180})", re.I)
    for chunk in chunks:
        for match in obligation_pattern.finditer(chunk.text):
            phrase = " ".join(match.group(1).split())
            obligations.append(Obligation(party="Unassigned", obligation=phrase,
                evidence=[Evidence(location=chunk.location, quote=phrase)]))
            if len(obligations) >= 30:
                break
        if len(obligations) >= 30:
            break
    return ContractAnalysis(document_name=filename, analysis_mode="rules-based",
        summary=f"Baseline analysis reviewed {len(chunks)} text sections. It detected {len(detected)} clause categories and {len(findings)} review prompts. Findings are heuristic and should be checked against the original agreement.",
        parties=parties, contract_value=amounts[0] if amounts else None,
        clauses_detected=sorted(set(detected)), obligations=obligations, findings=findings)


def analyze(filename: str, chunks: list[TextChunk]) -> ContractAnalysis:
    if not settings.openai_api_key:
        return rules_analysis(filename, chunks)
    full = "\\n\\n".join(f"[{c.location}]\\n{c.text}" for c in chunks)
    full = full[:60000]
    instructions = """Analyze this contract for business review. Return ONLY JSON with keys:
summary, parties, effective_date, end_date, governing_law, contract_value, currency,
clauses_detected, obligations, findings. Obligations have party, obligation, deadline,
evidence[{location,quote}]. Findings have category,title,severity (high|medium|low|info),
explanation,recommendation,evidence[{location,quote}]. Cite only exact excerpts from supplied
text and preserve location labels. Use null or empty lists for unknowns. Do not infer legal facts.
This is issue-spotting, not legal advice."""
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(model=settings.openai_model, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": instructions}, {"role": "user", "content": full}])
    data = json.loads(response.choices[0].message.content or "{}")
    data.update(document_name=filename, analysis_mode="openai", analyzed_at=datetime.utcnow())
    return ContractAnalysis.model_validate(data)
