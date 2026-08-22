from unittest.mock import patch

from langchain_core.documents import Document

from app.rag.evidence import (
    check_retrieval_evidence,
)
from app.rag.agent import (
    _deduplicate_results,
)
from app.rag.citations import (
    build_citations,
)


# ============================================================
# Helpers
# ============================================================

def make_document(
    *,
    document_id="00000000-0000-0000-0000-000000000001",
    filename="Stock_Market_Performance_2024.pdf",
    page=1,
    chunk_index=1,
    content="Apple's stock increased approximately 36% in 2024.",
):
    return Document(
        page_content=content,
        metadata={
            "document_id": document_id,
            "filename": filename,
            "page": page,
            "chunk_index": chunk_index,
            "user_id": "test-user-001",
        },
    )


# ============================================================
# Evidence Gate
# ============================================================

def test_evidence_gate_accepts_relevant_evidence():

    document = make_document()

    ranked_results = [
        (document, 0.80),
    ]

    result = check_retrieval_evidence(
        ranked_results=ranked_results,
        threshold=0.30,
    )

    assert result.sufficient is True
    assert result.best_score == 0.80

    assert result.ranked_results == ranked_results


def test_evidence_gate_rejects_unrelated_evidence():

    document = make_document(
        content="The weather in London was cloudy.",
    )

    ranked_results = [
        (document, 0.10),
    ]

    result = check_retrieval_evidence(
        ranked_results=ranked_results,
        threshold=0.30,
    )

    assert result.sufficient is False
    assert result.best_score == 0.10

    # Failed evidence must NOT be passed forward.
    assert result.ranked_results == []


def test_evidence_gate_uses_best_score():

    document_1 = make_document(
        chunk_index=1,
    )

    document_2 = make_document(
        chunk_index=2,
    )

    ranked_results = [
        (document_1, 0.10),
        (document_2, 0.75),
    ]

    result = check_retrieval_evidence(
        ranked_results=ranked_results,
        threshold=0.30,
    )

    assert result.sufficient is True
    assert result.best_score == 0.75


# ============================================================
# Evidence Deduplication
# ============================================================

def test_duplicate_chunks_are_removed():

    document = make_document(
        chunk_index=5,
    )

    duplicate = make_document(
        chunk_index=5,
        content=document.page_content,
    )

    ranked_results = [
        (document, 0.90),
        (duplicate, 0.80),
    ]

    result = _deduplicate_results(
        ranked_results,
    )

    assert len(result) == 1

    assert result[0][0].metadata["chunk_index"] == 5
    assert result[0][1] == 0.90


def test_different_chunks_are_not_removed():

    document_1 = make_document(
        chunk_index=5,
    )

    document_2 = make_document(
        chunk_index=6,
        content="Apple traded at approximately 40 times trailing earnings.",
    )

    ranked_results = [
        (document_1, 0.90),
        (document_2, 0.80),
    ]

    result = _deduplicate_results(
        ranked_results,
    )

    assert len(result) == 2


# ============================================================
# Citation Deduplication
# ============================================================

def test_citations_deduplicate_same_document_and_page():

    document_1 = make_document(
        page=1,
        chunk_index=5,
    )

    document_2 = make_document(
        page=1,
        chunk_index=6,
        content="Apple traded at approximately 40 times trailing earnings.",
    )

    ranked_results = [
        (document_1, 0.90),
        (document_2, 0.80),
    ]

    citations = build_citations(
        ranked_results,
    )

    assert len(citations) == 1

    assert citations[0].document_id == "00000000-0000-0000-0000-000000000001"
    assert citations[0].filename == (
        "Stock_Market_Performance_2024.pdf"
    )
    assert citations[0].page == 2


def test_citations_keep_different_pages():

    document_1 = make_document(
        page=1,
        chunk_index=5,
    )

    document_2 = make_document(
        page=4,
        chunk_index=14,
        content="Tesla's stock increased approximately 63%.",
    )

    ranked_results = [
        (document_1, 0.90),
        (document_2, 0.80),
    ]

    citations = build_citations(
        ranked_results,
    )

    assert len(citations) == 2

    assert citations[0].page == 2
    assert citations[1].page == 5


def test_citations_skip_missing_required_metadata():

    document = Document(
        page_content="Some content.",
        metadata={
            "page": 1,
            "chunk_index": 2,
        },
    )

    ranked_results = [
        (document, 0.90),
    ]

    citations = build_citations(
        ranked_results,
    )

    assert citations == []
    


# ============================================================
# Query API → Citation Integration
# ============================================================

def test_query_returns_citations_from_accepted_evidence(
    client,
    auth_headers,
    ready_document,
):

    accepted_document = make_document(
        document_id="00000000-0000-0000-0000-000000000002",
        page=1,
        chunk_index=5,
    )

    with patch(
        "app.api.query.ask_agent_with_trace"
    ) as mock_agent, patch(
        "app.api.query.get_user_chunks"
    ) as mock_chunks:

        mock_chunks.return_value = [accepted_document]

        mock_agent.return_value = {
            "answer": "Apple's stock increased approximately 36%.",
            "retrieved_results": [
                (accepted_document, 0.90),
            ],
        }

        response = client.post(
            "/api/query",
            json={
                "question": (
                    "Which company had a 36% stock increase?"
                )
            },
            headers=auth_headers,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == (
        "Apple's stock increased approximately 36%."
    )

    assert len(data["sources"]) == 1

    source = data["sources"][0]

    assert source["document_id"] == "00000000-0000-0000-0000-000000000002"
    assert source["filename"] == (
        "Stock_Market_Performance_2024.pdf"
    )
    assert source["page"] == 2
    assert source["chunk_index"] == 5


def test_query_returns_no_sources_when_evidence_fails(
    client,
    auth_headers,
    indexed_documents,
):

    with patch(
        "app.api.query.ask_agent_with_trace"
    ) as mock_agent:

        mock_agent.return_value = {
            "answer": (
                "I don't have the answer based on "
                "the provided documents."
            ),
            "retrieved_results": [],
        }

        response = client.post(
            "/api/query",
            json={
                "question": "Who won the FIFA World Cup?"
            },
            headers=auth_headers,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == (
        "I don't have the answer based on "
        "the provided documents."
    )

    assert data["sources"] == []