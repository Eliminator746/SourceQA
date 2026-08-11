from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
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
    current_user: User = Depends(get_current_user)
):

    # RAG implementation will be added later.

    return {
        "answer": "RAG pipeline is not implemented yet.",
        "sources": []
    }