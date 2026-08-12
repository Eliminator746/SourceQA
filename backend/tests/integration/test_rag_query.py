# tests/integration/test_rag_query.py

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.api.query import get_current_user
from app.rag.retrieval import retrieve


client = TestClient(app)


def test_rag_retrieval_integration(
    indexed_documents
):

    question = (
        "Which companies in the report experienced "
        "strong stock-price growth despite relatively "
        "weak or declining fundamentals?"
    )

    results = retrieve(
        question=question,
        documents=indexed_documents,
        user_id="test-user-001"
    )

    assert results
    assert len(results) <= 5

    # At least one result should mention Tesla,
    # based on the document/question being tested.
    
    combined_text = " ".join(
        document.page_content
        for document, score in results
    ).lower()

    assert "tesla" in combined_text
        

def test_rag_query_integration(
    client,
    auth_headers,
    indexed_documents
):

    question = (
        "Which companies in the report experienced "
        "strong stock-price growth despite relatively "
        "weak or declining fundamentals?"
    )

    response = client.post(
        "/api/query",
        headers=auth_headers,
        json={"question": question},
    )

    assert response.status_code == 200

    data = response.json()

    assert "answer" in data
    assert data["answer"]

    assert "sources" in data
    
    
    
def test_rag_query_returns_no_answer_for_unknown_question(
    client,
    auth_headers,
    indexed_documents
):

    question = (
        "What is the capital of Japan?"
    )

    response = client.post(
        "/api/query",
        headers=auth_headers,
        json={"question": question},
    )

    assert response.status_code == 200

    data = response.json()

    assert "answer" in data
    
    
    

from app.rag.evidence import check_retrieval_evidence
from app.rag.retrieval import retrieve


def test_retrieval_passes_evidence_gate(
    indexed_documents
):

    question = (
        "Which companies in the report experienced "
        "strong stock-price growth despite relatively "
        "weak or declining fundamentals?"
    )

    ranked_results = retrieve(
        question=question,
        documents=indexed_documents,
        user_id="test-user-001",
    )

    evidence = check_retrieval_evidence(
        ranked_results=ranked_results,
        threshold=0.30,
    )

    assert ranked_results
    assert evidence.sufficient is True
    assert evidence.best_score is not None
    
    

def test_retrieval_fails_evidence_gate_for_unrelated_question(
    indexed_documents
):

    question = (
        "What is the capital of Japan?"
    )

    ranked_results = retrieve(
        question=question,
        documents=indexed_documents,
        user_id="test-user-001",
    )

    evidence = check_retrieval_evidence(
        ranked_results=ranked_results,
        threshold=0.30,
    )

    assert evidence.sufficient is False