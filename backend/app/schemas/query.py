from uuid import UUID

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    conversation_id: UUID | None = Field(
        default=None,
        description=(
            "Conversation identifier. "
            "Omit this field to start a new conversation."
        ),
    )
    


class SourceResponse(BaseModel):
    document_id: UUID
    filename: str
    page: int | None = None
    chunk_index: int | None = None


class QueryResponse(BaseModel):
    conversation_id: UUID
    answer: str
    sources: list[SourceResponse]