from uuid import UUID

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str


class SourceResponse(BaseModel):
    document_id: UUID
    filename: str
    page: int | None = None
    chunk_index: int | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]