from unittest.mock import patch


def test_upload_pdf(client, auth_headers):

    file_content = b"%PDF-1.4 fake pdf content"

    with patch(
        "app.api.documents.s3_upload"
    ) as mock_upload:

        response = client.post(
            "/api/documents",
            headers=auth_headers,
            files={
                "file": (
                    "test.pdf",
                    file_content,
                    "application/pdf"
                )
            }
        )

    assert response.status_code == 201

    data = response.json()

    assert data["filename"] == "test.pdf"
    assert data["status"] == "processing"
    assert "document_id" in data

    mock_upload.assert_called_once()
    

def test_upload_pdf(client, auth_headers):

    file_content = b"fake pdf content"

    with patch(
        "app.api.documents.magic.from_buffer",
        return_value="application/pdf"
    ), patch(
        "app.api.documents.s3_upload"
    ) as mock_upload:

        response = client.post(
            "/api/documents",
            headers=auth_headers,
            files={
                "file": (
                    "test.pdf",
                    file_content,
                    "application/pdf"
                )
            }
        )

    assert response.status_code == 201

    data = response.json()

    assert data["filename"] == "test.pdf"
    assert data["status"] == "processing"

    mock_upload.assert_called_once()
    

def test_get_documents(
    client,
    auth_headers
):

    response = client.get(
        "/api/documents",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert "documents" in data
    assert "count" in data
    assert data["max_sources"] == 5
    

def test_get_documents_without_token(client):

    response = client.get(
        "/api/documents"
    )

    assert response.status_code == 401
    

def test_upload_unsupported_file(
    client,
    auth_headers
):

    file_content = b"fake executable"

    with patch(
        "app.api.documents.magic.from_buffer",
        return_value="application/x-executable"
    ):

        response = client.post(
            "/api/documents",
            headers=auth_headers,
            files={
                "file": (
                    "malware.exe",
                    file_content,
                    "application/octet-stream"
                )
            }
        )

    assert response.status_code == 400
    

def test_maximum_five_documents(
    client,
    auth_headers
):

    for i in range(5):

        with patch(
            "app.api.documents.magic.from_buffer",
            return_value="text/plain"
        ), patch(
            "app.api.documents.s3_upload"
        ):

            response = client.post(
                "/api/documents",
                headers=auth_headers,
                files={
                    "file": (
                        f"test_{i}.txt",
                        b"test document",
                        "text/plain"
                    )
                }
            )

        assert response.status_code == 201

    # Sixth document

    with patch(
        "app.api.documents.magic.from_buffer",
        return_value="text/plain"
    ):

        response = client.post(
            "/api/documents",
            headers=auth_headers,
            files={
                "file": (
                    "test_6.txt",
                    b"test document",
                    "text/plain"
                )
            }
        )

    assert response.status_code == 409
    
    
