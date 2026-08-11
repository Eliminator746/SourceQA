from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.query import router as query_router


app = FastAPI(
    title="RAG Q&A API",
    version="1.0.0"
)


app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(query_router)


@app.get("/")
def root():
    return {
        "message": "RAG Q&A API is running"
    }