"""Suggested integration test for the SSE endpoint."""

# Add a test similar to this to tests/integration/test_streaming_query.py.

from unittest.mock import patch


def test_query_stream_returns_sse_events(
    client,
    auth_headers,
    ready_document,
):
    async def fake_stream_agent_with_trace(**_kwargs):
        yield {"type": "status", "status": "searching"}
        yield {"type": "status", "status": "generating"}
        yield {"type": "token", "text": "Apple"}
        yield {"type": "token", "text": " saw 36% growth."}
        yield {
            "type": "complete",
            "answer": "Apple saw 36% growth.",
            "retrieved_results": [],
        }

    with patch(
        "app.api.query.get_user_chunks",
        return_value=[ready_document],
    ), patch(
        "app.api.query.stream_agent_with_trace",
        fake_stream_agent_with_trace,
    ):
        response = client.post(
            "/api/query/stream",
            json={
                "question": "How did Apple perform?",
            },
            headers=auth_headers,
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/event-stream"
    )

    body = response.text

    assert "event: conversation" in body
    assert "event: status" in body
    assert "event: token" in body
    assert '"text": "Apple"' in body
    assert "event: sources" in body
    assert "event: done" in body
