from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.document import Document
from app.models.user import User
from app.rag.agent import ask_agent_with_trace
from app.rag.citations import build_citations
from app.schemas.query import (
    QueryRequest,
    QueryResponse,
)


router = APIRouter(
    prefix="/api/query",
    tags=["Query"]
)


@router.post(
    "",
    response_model=QueryResponse
)
def query_documents(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.status == "ready",
        )
        .all()
    )

    if not documents:
        return {
            "answer": "I don't have the answer based on the provided documents.",
            "sources": [],
        }

    result = ask_agent_with_trace(
        question=request.question,
        documents=documents,
        user_id=str(current_user.id),
    )

    citations = build_citations(result["retrieved_results"])

    return {
        "answer": result["answer"],
        "sources": citations,
    }