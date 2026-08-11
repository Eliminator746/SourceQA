import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app



# @pytest.fixture
# def client():

#     with TestClient(app) as test_client:
#         yield test_client
        
        
        
@pytest.fixture
def client():

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user(client):

    email = f"test_{uuid.uuid4()}@example.com"
    password = "TestPassword123!"

    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 201

    return {
        "email": email,
        "password": password
    }


@pytest.fixture
def auth_headers(client, test_user):

    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }