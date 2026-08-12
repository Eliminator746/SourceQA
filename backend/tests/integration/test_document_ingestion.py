# tests/integration/test_document_ingestion.py

from pathlib import Path

from app.rag.loaders import load_document
from app.rag.ingestion import (
    ingest_documents,
    vector_store
)


def test_pdf_document_ingestion():

    pdf_path = Path(r"C:\Users\anish\Downloads\Stock_Market_Performance_2024.pdf")


    with open(pdf_path, "rb") as file:
        contents = file.read()

    document_id = "integration-test-document"
    user_id = "integration-test-user"

    # -----------------------------------------
    # Load PDF
    # -----------------------------------------

    documents = load_document(
        contents=contents,
        file_type="pdf",
        document_id=document_id,
        user_id=user_id,
        filename=pdf_path.name
    )

    assert documents
    assert len(documents) > 0

    # -----------------------------------------
    # Verify LangChain Documents
    # -----------------------------------------

    assert all(
        document.page_content
        for document in documents
    )

    assert all(
        document.metadata["document_id"]
        == document_id
        for document in documents
    )

    # -----------------------------------------
    # Ingest
    # -----------------------------------------

    chunks = ingest_documents(
        documents
    )

    assert chunks
    assert len(chunks) > 0

    # -----------------------------------------
    # Verify chunk metadata
    # -----------------------------------------

    for chunk in chunks:

        assert (
            chunk.metadata["document_id"]
            == document_id
        )

        assert (
            chunk.metadata["user_id"]
            == user_id
        )

        assert (
            "chunk_index"
            in chunk.metadata
        )

    # -----------------------------------------
    # Verify Chroma
    # -----------------------------------------

    stored = vector_store.get(
        where={
            "document_id": document_id
        }
    )

    assert stored["ids"]

    assert len(
        stored["ids"]
    ) == len(chunks)