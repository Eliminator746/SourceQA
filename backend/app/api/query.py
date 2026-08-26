import asyncio
import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.document import Document
from app.models.user import User
from app.rag.agent import (
    ask_agent_with_trace,
    stream_agent_with_trace,
)
from app.rag.citations import build_citations
from app.rag.ingestion import get_user_chunks
from app.schemas.query import QueryRequest, QueryResponse


router = APIRouter(
    prefix="/api/query",
    tags=["Query"],
)


NO_ANSWER = (
    "I don't have the answer based on the provided documents."
)


def _sse_event(event: str, data: dict) -> str:
    """Encode a dictionary as a Server-Sent Event."""

    payload = json.dumps(
        data,
        ensure_ascii=False,
    )

    return (
        f"event: {event}\n"
        f"data: {payload}\n\n"
    )


@router.post(
    "",
    response_model=QueryResponse,
)
def query_documents(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Existing non-streaming query endpoint."""

    ready_count = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.status == "ready",
        )
        .count()
    )

    conversation_id = (
        request.conversation_id
        or uuid.uuid4()
    )

    if not ready_count:
        return {
            "conversation_id": str(conversation_id),
            "answer": NO_ANSWER,
            "sources": [],
        }

    chunks = get_user_chunks(
        user_id=str(current_user.id)
    )

    if not chunks:
        return {
            "conversation_id": str(conversation_id),
            "answer": NO_ANSWER,
            "sources": [],
        }

    result = ask_agent_with_trace(
        question=request.question,
        documents=chunks,
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
    )

    citations = build_citations(
        result["retrieved_results"]
    )

    return {
        "conversation_id": str(conversation_id),
        "answer": result["answer"],
        "sources": citations,
    }


@router.post("/stream")
def query_documents_stream(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Streaming conversational RAG endpoint.

    The endpoint uses SSE over POST so the frontend can send both the
    current question and conversation_id while receiving incremental
    status/token/source events.
    """

    ready_count = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.status == "ready",
        )
        .count()
    )

    conversation_id = (
        request.conversation_id
        or uuid.uuid4()
    )

    async def event_stream() -> AsyncIterator[str]:
        yield _sse_event(
            "conversation",
            {
                "conversation_id": str(conversation_id),
            },
        )

        yield _sse_event(
            "status",
            {
                "status": "searching",
            },
        )

        if not ready_count:
            yield _sse_event(
                "token",
                {"text": NO_ANSWER},
            )
            yield _sse_event(
                "sources",
                {"sources": []},
            )
            yield _sse_event(
                "done",
                {
                    "conversation_id": str(conversation_id),
                    "sources": [],
                },
            )
            return

        try:
            # get_user_chunks is synchronous and can perform I/O / vector
            # store work, so keep it off the event loop.
            chunks = await asyncio.to_thread(
                get_user_chunks,
                user_id=str(current_user.id),
            )

            if not chunks:
                yield _sse_event(
                    "token",
                    {"text": NO_ANSWER},
                )
                yield _sse_event(
                    "sources",
                    {"sources": []},
                )
                yield _sse_event(
                    "done",
                    {
                        "conversation_id": str(conversation_id),
                        "sources": [],
                    },
                )
                return

            async for event in stream_agent_with_trace(
                question=request.question,
                documents=chunks,
                user_id=str(current_user.id),
                conversation_id=str(conversation_id),
            ):
                event_type = event.get("type")

                if event_type == "status":
                    yield _sse_event(
                        "status",
                        {
                            "status": event["status"],
                        },
                    )
                    continue

                if event_type == "token":
                    yield _sse_event(
                        "token",
                        {
                            "text": event["text"],
                        },
                    )
                    continue

                if event_type == "complete":
                    citations = build_citations(
                        event["retrieved_results"]
                    )

                    sources = [
                        {
                            "document_id": citation.document_id,
                            "filename": citation.filename,
                            "page": citation.page,
                            "chunk_index": citation.chunk_index,
                        }
                        for citation in citations
                    ]

                    yield _sse_event(
                        "sources",
                        {
                            "sources": sources,
                        },
                    )

                    yield _sse_event(
                        "done",
                        {
                            "conversation_id": str(conversation_id),
                            "sources": sources,
                        },
                    )

        except Exception as exc:
            # The response is already a 200 streaming response, so surface
            # runtime errors as an SSE error event rather than crashing the UI.
            yield _sse_event(
                "error",
                {
                    "message": (
                        "Something went wrong while generating the answer."
                    )
                },
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
