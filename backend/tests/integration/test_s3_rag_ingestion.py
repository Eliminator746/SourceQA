from unittest.mock import MagicMock, patch

from app.services.rag_ingestion import (
    ingest_document_from_s3,
)


def test_s3_to_rag_ingestion(
    db_session,
    test_document,
):

    fake_pdf = b"Test PDF content"
    loaded_documents = [MagicMock()]
    chunks = [MagicMock()]

    with patch(
        "app.services.rag_ingestion.get_s3_object",
        return_value=fake_pdf,
    ), patch(
        "app.services.rag_ingestion.load_document",
        return_value=loaded_documents,
    ), patch(
        "app.services.rag_ingestion.ingest_documents",
        return_value=chunks,
    ):

        ingest_document_from_s3(
            document=test_document,
            db=db_session,
        )

    db_session.refresh(test_document)

    assert test_document.status == "ready"
    assert test_document.error_message is None