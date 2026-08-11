def test_query_requires_authentication(client):

    response = client.post(
        "/api/query",
        json={
            "question": "What is the leave policy?"
        }
    )

    assert response.status_code == 401
    

def test_query(
    client,
    auth_headers
):

    response = client.post(
        "/api/query",
        headers=auth_headers,
        json={
            "question": "What is the leave policy?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)
    
    

def test_empty_question(
    client,
    auth_headers
):

    response = client.post(
        "/api/query",
        headers=auth_headers,
        json={
            "question": ""
        }
    )

    assert response.status_code == 422
    

def test_question_too_long(
    client,
    auth_headers
):

    question = "a" * 1001

    response = client.post(
        "/api/query",
        headers=auth_headers,
        json={
            "question": question
        }
    )

    assert response.status_code == 422

