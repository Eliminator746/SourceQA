from langchain_core.documents import Document

from app.rag.citations import (
    build_citations,
    Citation,
)


def test_build_citations():

    document = Document(
        page_content="Tesla gained 63% in 2024.",
        metadata={
            "document_id": "doc-123",
            "filename": "Stock_Market_Performance_2024.pdf",
            "page": 4,
            "chunk_index": 7,
        },
    )

    results = [
        (document, 0.87)
    ]

    citations = build_citations(
        ranked_results=results
    )

    assert len(citations) == 1

    assert citations[0] == Citation(
        document_id="doc-123",
        filename="Stock_Market_Performance_2024.pdf",
        page=5,
        chunk_index=7,
    )


def test_duplicate_chunks_same_page_create_one_citation():

    document_1 = Document(
        page_content="Chunk 1",
        metadata={
            "document_id": "doc-123",
            "filename": "report.pdf",
            "page": 4,
            "chunk_index": 1,
        },
    )

    document_2 = Document(
        page_content="Chunk 2",
        metadata={
            "document_id": "doc-123",
            "filename": "report.pdf",
            "page": 4,
            "chunk_index": 2,
        },
    )

    results = [
        (document_1, 0.90),
        (document_2, 0.80),
    ]

    citations = build_citations(results)

    assert len(citations) == 1
    assert citations[0].page == 5


def test_multiple_pages_create_multiple_citations():

    document_1 = Document(
        page_content="Page 5 content",
        metadata={
            "document_id": "doc-123",
            "filename": "report.pdf",
            "page": 4,
        },
    )

    document_2 = Document(
        page_content="Page 6 content",
        metadata={
            "document_id": "doc-123",
            "filename": "report.pdf",
            "page": 5,
        },
    )

    results = [
        (document_1, 0.90),
        (document_2, 0.80),
    ]

    citations = build_citations(results)

    assert len(citations) == 2

    assert citations[0].page == 5
    assert citations[1].page == 6


def test_empty_results_return_no_citations():

    citations = build_citations([])

    assert citations == []


def test_missing_metadata_is_not_cited():

    document = Document(
        page_content="Some content",
        metadata={}
    )

    citations = build_citations(
        [(document, 0.8)]
    )

    assert citations == []