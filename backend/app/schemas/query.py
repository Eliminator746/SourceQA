from uuid import UUID

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class SourceResponse(BaseModel):
    document_id: UUID
    filename: str
    page: int | None = None
    chunk_index: int | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]