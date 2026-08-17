from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.query import router as query_router
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RAG Q&A API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(query_router)


@app.get("/")
def root():
    return {
        "message": "RAG Q&A API is running"
    }