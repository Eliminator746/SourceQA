import pytest
from langchain_core.documents import Document

from app.rag.evidence import check_retrieval_evidence


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def _ranked(documents, scores):
    return list(zip(documents, scores))


# ---------------------------------------------------------
# 1. Strong evidence should pass
# ---------------------------------------------------------

def test_evidence_gate_accepts_strong_evidence():

    document = Document(
        page_content=(
            "Tesla's stock price increased "
            "approximately 63% in 2024."
        ),
        metadata={
            "filename": "Stock_Market_Performance_2024.pdf",
            "page": 8,
        },
    )

    result = check_retrieval_evidence(
        ranked_results=[(document, 0.85)],
        threshold=0.30,
    )

    assert result.sufficient is True
    assert result.best_score == 0.85
    assert len(result.ranked_results) == 1


# ---------------------------------------------------------
# 2. Weak evidence should fail
# ---------------------------------------------------------

def test_evidence_gate_rejects_weak_evidence():

    document = Document(
        page_content=(
            "The company reported moderate "
            "growth during the year."
        ),
        metadata={
            "filename": "Stock_Market_Performance_2024.pdf",
            "page": 15,
        },
    )

    result = check_retrieval_evidence(
        ranked_results=[(document, 0.12)],
        threshold=0.30,
    )

    assert result.sufficient is False
    assert result.best_score == 0.12
    assert result.ranked_results == []


# ---------------------------------------------------------
# 3. No documents should fail
# ---------------------------------------------------------

def test_evidence_gate_rejects_no_documents():

    result = check_retrieval_evidence(
        ranked_results=[],
        threshold=0.30,
    )

    assert result.sufficient is False
    assert result.ranked_results == []
    assert result.best_score is None


# ---------------------------------------------------------
# 4. Multiple documents — best score determines acceptance
# ---------------------------------------------------------

def test_evidence_gate_uses_best_score():

    documents = [
        Document(page_content="Weak evidence"),
        Document(page_content="Moderate evidence"),
        Document(page_content="Strong evidence"),
    ]

    result = check_retrieval_evidence(
        ranked_results=_ranked(documents, [0.12, 0.42, 0.81]),
        threshold=0.30,
    )

    assert result.sufficient is True
    assert result.best_score == 0.81
    assert len(result.ranked_results) == 3


# ---------------------------------------------------------
# 5. All evidence below threshold
# ---------------------------------------------------------

def test_evidence_gate_rejects_when_all_scores_are_low():

    documents = [
        Document(page_content="Evidence 1"),
        Document(page_content="Evidence 2"),
        Document(page_content="Evidence 3"),
    ]

    result = check_retrieval_evidence(
        ranked_results=_ranked(documents, [0.10, 0.18, 0.25]),
        threshold=0.30,
    )

    assert result.sufficient is False
    assert result.best_score == 0.25
    assert result.ranked_results == []


# ---------------------------------------------------------
# 6. Exact threshold should pass
# ---------------------------------------------------------

def test_evidence_gate_accepts_exact_threshold():

    document = Document(
        page_content="Evidence exactly at threshold"
    )

    result = check_retrieval_evidence(
        ranked_results=[(document, 0.30)],
        threshold=0.30,
    )

    assert result.sufficient is True
    assert result.best_score == 0.30


# ---------------------------------------------------------
# 7. Non-Document object raises TypeError
# ---------------------------------------------------------

def test_evidence_gate_rejects_non_document():

    with pytest.raises(TypeError):
        check_retrieval_evidence(
            ranked_results=[("not a document", 0.80)],
            threshold=0.30,
        )


# ---------------------------------------------------------
# 8. check_retrieval_evidence with ranked_results tuple form
# ---------------------------------------------------------

def test_check_retrieval_evidence():

    documents = [
        Document(page_content="Tesla stock increased strongly."),
        Document(page_content="Tesla earnings declined."),
    ]

    ranked_results = [
        (documents[0], 0.87),
        (documents[1], 0.72),
    ]

    result = check_retrieval_evidence(
        ranked_results=ranked_results,
        threshold=0.30,
    )

    assert result.sufficient is True
    assert result.best_score == 0.87
    assert len(result.ranked_results) == 2