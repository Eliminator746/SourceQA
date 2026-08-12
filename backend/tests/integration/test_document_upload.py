# tests/integration/test_document_upload.py

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.api.documents import get_current_user
from app.models.document import Document


client = TestClient(app)


def test_document_upload_integration(
    db_session,
    test_user,
    monkeypatch
):
    """
    Integration test:

    API
      -> authentication
      -> file validation
      -> S3 upload
      -> database record
    """

    # -----------------------------------------
    # Mock authenticated user
    # -----------------------------------------

    app.dependency_overrides[get_current_user] = (
        lambda: test_user
    )

    # -----------------------------------------
    # Mock S3
    # -----------------------------------------

    mock_s3 = MagicMock()

    monkeypatch.setattr(
        "app.services.s3_service.s3_client",
        mock_s3
    )

    # -----------------------------------------
    # Test PDF
    # -----------------------------------------

    pdf_content = (
        b"%PDF-1.4\n"
        b"Fake PDF content for integration testing"
    )

    response = client.post(
        "/api/documents",
        files={
            "file": (
                "test.pdf",
                pdf_content,
                "application/pdf"
            )
        }
    )

    # -----------------------------------------
    # API response
    # -----------------------------------------

    assert response.status_code in [200, 201]

    data = response.json()

    # The API returns `document_id` for the created document
    assert "document_id" in data
    assert data["filename"] == "test.pdf"

    # -----------------------------------------
    # S3 was called
    # -----------------------------------------

    mock_s3.put_object.assert_called_once()

    # -----------------------------------------
    # Database record exists
    # -----------------------------------------

    document = (
        db_session.query(Document)
        .filter(
            Document.filename == "test.pdf"
        )
        .first()
    )

    assert document is not None
    assert document.user_id == test_user.id
    assert document.s3_key is not None

    # -----------------------------------------
    # Cleanup
    # -----------------------------------------

    app.dependency_overrides.clear()