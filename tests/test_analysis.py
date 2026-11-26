from contractiq.analysis import rules_analysis
from contractiq.extraction import TextChunk


def test_rules_analysis_finds_demo_review_topics():
    chunks = [TextChunk(location="Page 1", text=(
        "Provider's liability is unlimited and without limitation. "
        "This agreement shall automatically renew for successive one-year periods. "
        "Provider shall indemnify Customer against any and all claims."
    ))]
    result = rules_analysis("sample.pdf", chunks)
    categories = {finding.category for finding in result.findings}
    assert "liability" in categories
    assert "renewal" in categories
    assert "indemnity" in categories
    assert all(finding.evidence for finding in result.findings if finding.category != "governing law")


def test_missing_governing_law_is_flagged():
    result = rules_analysis("sample.pdf", [TextChunk(location="Page 1", text="Provider shall deliver services.")])
    assert any(f.category == "governing law" for f in result.findings)
