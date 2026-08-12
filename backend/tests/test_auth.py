import uuid


def test_register_user(client):

    email = f"newuser_{uuid.uuid4()}@example.com"

    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Password123!"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email
    assert "id" in data
    assert "created_at" in data

    # Password must never be returned
    assert "password" not in data
    assert "password_hash" not in data
    

def test_duplicate_registration(client):

    email = f"duplicate_{uuid.uuid4()}@example.com"
    payload = {"email": email, "password": "Password123!"}

    first_response = client.post("/api/auth/register", json=payload)

    assert first_response.status_code == 201

    second_response = client.post("/api/auth/register", json=payload)

    assert second_response.status_code == 409

    assert second_response.json()["detail"] == "Email already registered"
    
def test_login(client, test_user):

    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, test_user):

    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401

    assert (
        response.json()["detail"]
        == "Incorrect email or password"
    )
    

def test_login_nonexistent_user(client):

    response = client.post(
        "/api/auth/login",
        json={
            "email": "doesnotexist@example.com",
            "password": "Password123!"
        }
    )

    assert response.status_code == 401
    
def test_get_current_user(
    client,
    test_user,
    auth_headers
):

    response = client.get(
        "/api/auth/me",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == test_user["email"]
    assert "id" in data
    

def test_me_without_token(client):

    response = client.get(
        "/api/auth/me"
    )

    assert response.status_code == 401