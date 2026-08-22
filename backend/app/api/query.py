import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.document import Document
from app.models.user import User
from app.rag.agent import ask_agent_with_trace
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


@router.post(
    "",
    response_model=QueryResponse,
)
def query_documents(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ========================================================
    # 1. Validate that the user has ready documents
    # ========================================================

    ready_count = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.status == "ready",
        )
        .count()
    )

    if not ready_count:
        # A new conversation does not need to be created
        # if there is no document corpus to query.
        return {
            "conversation_id": (
                request.conversation_id
                or uuid.uuid4()
            ),
            "answer": NO_ANSWER,
            "sources": [],
        }

    # ========================================================
    # 2. Load the user's indexed chunks
    # ========================================================

    chunks = get_user_chunks(
        user_id=str(current_user.id)
    )

    if not chunks:
        return {
            "conversation_id": (
                request.conversation_id
                or uuid.uuid4()
            ),
            "answer": NO_ANSWER,
            "sources": [],
        }

    # ========================================================
    # 3. Resolve conversation ID
    # ========================================================
    #
    # Existing conversation:
    #
    #     request.conversation_id
    #             ↓
    #        same thread
    #
    # New conversation:
    #
    #     None
    #       ↓
    #     generate UUID
    #       ↓
    #     new thread
    #
    # ========================================================

    conversation_id = (
        request.conversation_id
        or uuid.uuid4()
    )

    # ========================================================
    # 4. Run conversational RAG agent
    # ========================================================

    result = ask_agent_with_trace(
        question=request.question,
        documents=chunks,
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
    )

    # ========================================================
    # 5. Build citations
    # ========================================================

    citations = build_citations(
        result["retrieved_results"]
    )

    # ========================================================
    # 6. Return response
    # ========================================================

    return {
        "conversation_id": str(conversation_id),
        "answer": result["answer"],
        "sources": citations,
    }