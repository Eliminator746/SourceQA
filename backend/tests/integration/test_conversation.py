from unittest.mock import patch

from langchain_core.documents import Document


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
# New conversation
# ============================================================

def test_query_creates_conversation_id(
    client,
    auth_headers,
    ready_document,
):
    document = make_document()

    with patch(
        "app.api.query.get_user_chunks"
    ) as mock_chunks, patch(
        "app.api.query.ask_agent_with_trace"
    ) as mock_agent:

        mock_chunks.return_value = [document]

        mock_agent.return_value = {
            "answer": "Apple saw approximately 36% growth.",
            "retrieved_results": [
                (document, 0.90),
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

    assert data["conversation_id"] is not None
    assert isinstance(
        data["conversation_id"],
        str,
    )


# ============================================================
# Explicit conversation ID is preserved
# ============================================================

def test_query_preserves_conversation_id(
    client,
    auth_headers,
    ready_document,
):
    document = make_document()

    conversation_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    with patch(
        "app.api.query.get_user_chunks"
    ) as mock_chunks, patch(
        "app.api.query.ask_agent_with_trace"
    ) as mock_agent:

        mock_chunks.return_value = [document]

        mock_agent.return_value = {
            "answer": "Apple saw approximately 36% growth.",
            "retrieved_results": [
                (document, 0.90),
            ],
        }

        response = client.post(
            "/api/query",
            json={
                "question": (
                    "Which company had a 36% stock increase?"
                ),
                "conversation_id": conversation_id,
            },
            headers=auth_headers,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["conversation_id"] == conversation_id

    mock_agent.assert_called_once()

    call_kwargs = mock_agent.call_args.kwargs

    assert call_kwargs["conversation_id"] == conversation_id


# ============================================================
# Follow-up uses the same conversation
# ============================================================

def test_followup_uses_same_conversation(
    client,
    auth_headers,
    ready_document,
):
    document = make_document()

    conversation_id = (
        "22222222-2222-2222-2222-222222222222"
    )

    with patch(
        "app.api.query.get_user_chunks"
    ) as mock_chunks, patch(
        "app.api.query.ask_agent_with_trace"
    ) as mock_agent:

        mock_chunks.return_value = [document]

        mock_agent.side_effect = [
            {
                "answer": (
                    "Apple saw approximately 36% growth."
                ),
                "retrieved_results": [
                    (document, 0.90),
                ],
            },
            {
                "answer": (
                    "Apple traded at approximately "
                    "40 times trailing earnings."
                ),
                "retrieved_results": [
                    (document, 0.90),
                ],
            },
        ]

        # ----------------------------------------------------
        # First turn
        # ----------------------------------------------------

        first_response = client.post(
            "/api/query",
            json={
                "question": (
                    "Which company had a 36% stock increase?"
                ),
                "conversation_id": conversation_id,
            },
            headers=auth_headers,
        )

        assert first_response.status_code == 200

        # ----------------------------------------------------
        # Follow-up turn
        # ----------------------------------------------------

        second_response = client.post(
            "/api/query",
            json={
                "question": (
                    "What was its valuation?"
                ),
                "conversation_id": conversation_id,
            },
            headers=auth_headers,
        )

        assert second_response.status_code == 200

    assert (
        first_response.json()["conversation_id"]
        == conversation_id
    )

    assert (
        second_response.json()["conversation_id"]
        == conversation_id
    )

    assert mock_agent.call_count == 2

    first_call = mock_agent.call_args_list[0].kwargs
    second_call = mock_agent.call_args_list[1].kwargs

    assert first_call["conversation_id"] == conversation_id
    assert second_call["conversation_id"] == conversation_id


# ============================================================
# Different conversations remain isolated
# ============================================================

def test_different_conversations_use_different_ids(
    client,
    auth_headers,
    ready_document,
):
    document = make_document()

    conversation_a = (
        "33333333-3333-3333-3333-333333333333"
    )

    conversation_b = (
        "44444444-4444-4444-4444-444444444444"
    )

    with patch(
        "app.api.query.get_user_chunks"
    ) as mock_chunks, patch(
        "app.api.query.ask_agent_with_trace"
    ) as mock_agent:

        mock_chunks.return_value = [document]

        mock_agent.return_value = {
            "answer": "Test answer.",
            "retrieved_results": [
                (document, 0.90),
            ],
        }

        # Conversation A
        response_a = client.post(
            "/api/query",
            json={
                "question": "Tell me about Apple.",
                "conversation_id": conversation_a,
            },
            headers=auth_headers,
        )

        # Conversation B
        response_b = client.post(
            "/api/query",
            json={
                "question": "Tell me about Tesla.",
                "conversation_id": conversation_b,
            },
            headers=auth_headers,
        )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    assert (
        response_a.json()["conversation_id"]
        == conversation_a
    )

    assert (
        response_b.json()["conversation_id"]
        == conversation_b
    )

    assert mock_agent.call_count == 2

    first_call = mock_agent.call_args_list[0].kwargs
    second_call = mock_agent.call_args_list[1].kwargs

    assert (
        first_call["conversation_id"]
        == conversation_a
    )

    assert (
        second_call["conversation_id"]
        == conversation_b
    )

    assert conversation_a != conversation_b


# ============================================================
# Conversation ID remains stable across multiple turns
# ============================================================

def test_conversation_id_remains_stable(
    client,
    auth_headers,
    ready_document,
):
    document = make_document()

    conversation_id = (
        "55555555-5555-5555-5555-555555555555"
    )

    with patch(
        "app.api.query.get_user_chunks"
    ) as mock_chunks, patch(
        "app.api.query.ask_agent_with_trace"
    ) as mock_agent:

        mock_chunks.return_value = [document]

        mock_agent.return_value = {
            "answer": "Test answer.",
            "retrieved_results": [
                (document, 0.90),
            ],
        }

        for question in [
            "Tell me about Apple.",
            "What about its valuation?",
            "How does that compare with Tesla?",
        ]:

            response = client.post(
                "/api/query",
                json={
                    "question": question,
                    "conversation_id": conversation_id,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200

            data = response.json()

            assert (
                data["conversation_id"]
                == conversation_id
            )

    assert mock_agent.call_count == 3

    for call in mock_agent.call_args_list:

        assert (
            call.kwargs["conversation_id"]
            == conversation_id
        )