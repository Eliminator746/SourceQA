from langchain_core.documents import Document

from app.rag.evidence import (
    check_evidence,
    check_retrieval_evidence,
)


# ---------------------------------------------------------
# 1. Strong evidence should pass
# ---------------------------------------------------------

def test_evidence_gate_accepts_strong_evidence():

    documents = [
        Document(
            page_content=(
                "Tesla's stock price increased "
                "approximately 63% in 2024."
            ),
            metadata={
                "filename": "Stock_Market_Performance_2024.pdf",
                "page": 8,
            },
        )
    ]

    scores = [0.85]

    result = check_evidence(
        documents=documents,
        scores=scores,
        threshold=0.30,
    )

    assert result.sufficient is True
    assert result.best_score == 0.85
    assert len(result.documents) == 1


# ---------------------------------------------------------
# 2. Weak evidence should fail
# ---------------------------------------------------------

def test_evidence_gate_rejects_weak_evidence():

    documents = [
        Document(
            page_content=(
                "The company reported moderate "
                "growth during the year."
            ),
            metadata={
                "filename": "Stock_Market_Performance_2024.pdf",
                "page": 15,
            },
        )
    ]

    scores = [0.12]

    result = check_evidence(
        documents=documents,
        scores=scores,
        threshold=0.30,
    )

    assert result.sufficient is False
    assert result.best_score == 0.12
    assert result.documents == []


# ---------------------------------------------------------
# 3. No documents should fail
# ---------------------------------------------------------

def test_evidence_gate_rejects_no_documents():

    result = check_evidence(
        documents=[],
        scores=[],
        threshold=0.30,
    )

    assert result.sufficient is False
    assert result.documents == []
    assert result.best_score is None


# ---------------------------------------------------------
# 4. Multiple documents
# ---------------------------------------------------------

def test_evidence_gate_uses_best_score():

    documents = [
        Document(page_content="Weak evidence"),
        Document(page_content="Moderate evidence"),
        Document(page_content="Strong evidence"),
    ]

    scores = [
        0.12,
        0.42,
        0.81,
    ]

    result = check_evidence(
        documents=documents,
        scores=scores,
        threshold=0.30,
    )

    assert result.sufficient is True
    assert result.best_score == 0.81

    assert len(result.documents) == 3


# ---------------------------------------------------------
# 5. All evidence below threshold
# ---------------------------------------------------------

def test_evidence_gate_rejects_when_all_scores_are_low():

    documents = [
        Document(page_content="Evidence 1"),
        Document(page_content="Evidence 2"),
        Document(page_content="Evidence 3"),
    ]

    scores = [
        0.10,
        0.18,
        0.25,
    ]

    result = check_evidence(
        documents=documents,
        scores=scores,
        threshold=0.30,
    )

    assert result.sufficient is False
    assert result.best_score == 0.25
    assert result.documents == []


# ---------------------------------------------------------
# 6. Exact threshold should pass
# ---------------------------------------------------------

def test_evidence_gate_accepts_exact_threshold():

    documents = [
        Document(
            page_content="Evidence exactly at threshold"
        )
    ]

    scores = [0.30]

    result = check_evidence(
        documents=documents,
        scores=scores,
        threshold=0.30,
    )

    assert result.sufficient is True
    assert result.best_score == 0.30


# ---------------------------------------------------------
# 7. Mismatched documents and scores
# ---------------------------------------------------------

def test_evidence_gate_rejects_mismatched_scores():

    documents = [
        Document(page_content="Evidence 1"),
        Document(page_content="Evidence 2"),
    ]

    scores = [0.80]

    try:
        check_evidence(
            documents=documents,
            scores=scores,
            threshold=0.30,
        )

        assert False, (
            "Expected ValueError for mismatched "
            "documents and scores"
        )

    except ValueError as exc:

        assert (
            str(exc)
            == "Number of documents must match "
               "number of scores."
        )


# ---------------------------------------------------------
# 8. Test the retrieval-result convenience function
# ---------------------------------------------------------

def test_check_retrieval_evidence():

    documents = [
        Document(
            page_content="Tesla stock increased strongly."
        ),
        Document(
            page_content="Tesla earnings declined."
        ),
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
    assert len(result.documents) == 2