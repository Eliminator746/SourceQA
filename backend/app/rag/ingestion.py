from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")


vector_store = Chroma(
    embedding_function=embeddings,
    persist_directory="./chroma_db",
    collection_name="rag_documents"
)


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
)


def delete_document_chunks(
    document_id: str,
) -> None:

    vector_store.delete(
        where={
            "document_id": document_id
        }
    )


def ingest_documents(
    documents: list[Document],
) -> list[Document]:

    if not documents:
        return []

    chunks = text_splitter.split_documents(
        documents
    )

    counters = defaultdict(int)

    for chunk in chunks:

        document_id = chunk.metadata["document_id"]

        chunk.metadata["chunk_index"] = (
            counters[document_id]
        )

        counters[document_id] += 1

    # -----------------------------------------
    # Create deterministic IDs
    # -----------------------------------------

    ids = []

    for chunk in chunks:

        document_id = chunk.metadata["document_id"]
        chunk_index = chunk.metadata["chunk_index"]

        ids.append(
            f"{document_id}_chunk_{chunk_index}"
        )

    # -----------------------------------------
    # Remove old vectors for this document
    # -----------------------------------------

    document_ids = {
        chunk.metadata["document_id"]
        for chunk in chunks
    }

    for document_id in document_ids:
        delete_document_chunks(document_id)

    # -----------------------------------------
    # Add new vectors
    # -----------------------------------------

    vector_store.add_documents(
        documents=chunks,
        ids=ids,
    )

    return chunks


def get_user_chunks(user_id: str) -> list[Document]:
    """
    Load all indexed chunks belonging to a user from Chroma.

    Used by the evaluation pipeline to reconstruct the evaluation
    corpus before running BM25 + semantic retrieval.
    """

    result = vector_store.get(
        where={
            "user_id": user_id
        },
        include=[
            "documents",
            "metadatas",
        ],
    )

    documents = []

    for page_content, metadata in zip(
        result.get("documents", []),
        result.get("metadatas", []),
    ):
        documents.append(
            Document(
                page_content=page_content,
                metadata=metadata or {},
            )
        )

    return documents



# Documents
#    ↓
# RecursiveCharacterTextSplitter
#    ↓
# Chunks
#    ↓
# HuggingFaceEmbeddings
#    ↓
# Chroma