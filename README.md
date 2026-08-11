# RAG Q&A — Source-Grounded Document Assistant

A full-stack Retrieval-Augmented Generation (RAG) application that allows users to upload up to **5 documents** and ask questions based exclusively on the information contained within those sources. It includes a login feature, so users can access their documents and continue asking questions anytime. When the 5-document limit is reached, users can delete an existing document and upload a new one.

The system supports **PDF, DOCX, and TXT** files, performs **hybrid retrieval using semantic and keyword search**, reranks the retrieved results, and generates concise answers with **source citations** for transparency.

If the requested information cannot be found in the user's uploaded sources, the application explicitly states that it does not have enough information to answer rather than relying on the model's general knowledge.

---

## Features

- 🔐 JWT-based user authentication
- 📄 Upload PDF, DOCX, and TXT documents
- 📚 Maximum of 5 active sources per user
- ☁️ Private document storage using Amazon S3
- 🗄️ PostgreSQL database hosted on Neon
- 🔎 Hybrid retrieval using:
  - Semantic vector search
  - BM25 keyword search
  - Reciprocal Rank Fusion (RRF)

- 🎯 Cross-encoder reranking
- 🤖 Source-grounded LLM responses
- 📑 Source/page citations with answers
- 🛡️ User-level document isolation
- 🚫 Prevents answering from information outside the provided sources
- ⚡ Token-efficient context construction
- 🧹 Complete document deletion from S3, vector store, and database
- 🖥️ React frontend
- 🚀 FastAPI backend
- 🧪 Automated API testing with pytest

---

# Architecture

```text
                         ┌─────────────────────┐
                         │       React UI      │
                         │                     │
                         │  Login              │
                         │  Sources            │
                         │  Q&A                │
                         └──────────┬──────────┘
                                    │
                              HTTP / JWT
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │                     │
                         │ Authentication      │
                         │ Document APIs       │
                         │ Query API           │
                         └───────┬─────┬───────┘
                                 │     │
                    ┌────────────┘     └──────────────┐
                    ▼                                 ▼
             ┌─────────────┐                  ┌─────────────┐
             │ PostgreSQL  │                  │  Amazon S3  │
             │   Neon DB   │                  │             │
             │             │                  │ PDF/DOCX/TXT│
             │ Users       │                  │   files     │
             │ Documents   │                  └─────────────┘
             └─────────────┘

                                    Document
                                    ingestion
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ Text Extraction  │
                              │                  │
                              │ PDF / DOCX / TXT │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │     Chunking     │
                              │                  │
                              │ Recursive Split  │
                              └────────┬─────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
                  ┌──────────────┐            ┌──────────────┐
                  │  Embeddings  │            │     BM25     │
                  └──────┬───────┘            └──────┬───────┘
                         │                           │
                         ▼                           ▼
                  ┌──────────────┐            ┌──────────────┐
                  │   ChromaDB   │            │ Keyword Index│
                  └──────┬───────┘            └──────┬───────┘
                         │                           │
                         └─────────────┬─────────────┘
                                       ▼
                              ┌──────────────────┐
                              │  Hybrid Search   │
                              │                  │
                              │ Semantic + BM25  │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │       RRF        │
                              │ Reciprocal Rank  │
                              │     Fusion       │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │    Reranker      │
                              │ Cross Encoder    │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ Evidence Check   │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │       LLM        │
                              │ Source Grounded  │
                              │     Answer       │
                              └────────┬─────────┘
                                       │
                                       ▼
                              Answer + Citations
```

---

# How It Works

## 1. Authentication

Users create an account and authenticate using JWT.

```text
Register
   ↓
Password hashing
   ↓
PostgreSQL
```

During login:

```text
Email + Password
       ↓
Verify password
       ↓
Generate JWT
       ↓
Client
```

The JWT is required for protected document and query endpoints.

Every request is associated with the authenticated user's ID.

---

# 2. Document Upload

Users can upload:

- PDF
- DOCX
- TXT

A user can have a maximum of **5 active documents**.

The upload flow is:

```text
User
 ↓
FastAPI
 ↓
Validate file size
 ↓
Validate actual MIME type
 ↓
Generate document UUID
 ↓
Upload original file to private S3
 ↓
Create PostgreSQL document record
 ↓
Start ingestion
```

S3 objects use a user-scoped structure:

```text
documents/{user_id}/{document_id}.{extension}
```

This keeps documents logically isolated between users.

---

# 3. Document Processing

Once a document is uploaded, the ingestion pipeline extracts its content.

```text
S3 Document
     ↓
Document Loader
     ↓
Extracted LangChain Documents
     ↓
Recursive Character Splitter
     ↓
Chunks
```

The supported loaders are:

### PDF

PDF pages are preserved so that citations can point back to the relevant page.

### DOCX

Paragraph content is extracted while retaining document metadata.

### TXT

Plain text is decoded and converted into LangChain documents.

Each chunk maintains metadata such as:

```json
{
  "document_id": "document-uuid",
  "user_id": "user-uuid",
  "filename": "HR_Handbook.pdf",
  "file_type": "pdf",
  "page": 14,
  "chunk_index": 5
}
```

This metadata is later used for:

- user-level retrieval isolation
- source attribution
- page citations
- document identification

---

# 4. Chunking

Documents are split using `RecursiveCharacterTextSplitter`.

The splitter attempts to preserve natural boundaries such as:

```text
Paragraph
   ↓
Line
   ↓
Sentence
   ↓
Word
```

Chunks contain a controlled overlap so that important information isn't lost between chunk boundaries.

The chunking strategy is designed to balance:

- retrieval quality
- contextual completeness
- number of retrieved chunks
- LLM token consumption

---

# 5. Embeddings and Vector Search

Each chunk is converted into an embedding vector.

```text
Chunk
  ↓
Embedding Model
  ↓
Vector
  ↓
ChromaDB
```

ChromaDB stores:

```text
Embedding
Text
Document ID
User ID
Filename
Page
Chunk index
```

At query time, semantic similarity is used to retrieve chunks that are conceptually relevant to the question.

---

# 6. BM25 Keyword Search

Semantic search isn't always enough.

Semantic retrieval can identify the relationship between these concepts, but keyword search is particularly useful when users search for:

- exact terms
- product names
- employee IDs
- technical terminology
- error codes
- specific phrases

Therefore the application also performs BM25 keyword retrieval.

---

# 7. Hybrid Search

The application combines:

```text
Semantic Search
       +
BM25 Search
```

The two retrieval methods return their own ranked results.

Example:

```text
Semantic Search
    → Top 20

BM25
    → Top 20
```

These results are combined using **Reciprocal Rank Fusion (RRF)**.

```text
Semantic Results
       +
BM25 Results
       ↓
      RRF
       ↓
Unified Ranking
```

This provides a stronger retrieval strategy than relying on either semantic or keyword search alone.

---

# 8. Reranking

The initial hybrid retrieval stage intentionally retrieves more candidates.

The candidates are then passed through a cross-encoder reranker.

```text
Hybrid Search
    ↓
Top candidates
    ↓
Cross Encoder
    ↓
Relevance scores
    ↓
Top relevant chunks
```

This allows the system to provide the LLM with only the most relevant evidence.

That improves both:

- answer quality
- token efficiency

---

# 9. Source-Grounded Answer Generation

The final retrieved chunks are provided to the LLM as context.

The model is instructed to:

1. Use only the supplied document context.
2. Never invent information.
3. Never rely on unrelated world knowledge.
4. Answer concisely.
5. Return an explicit fallback when evidence is insufficient.
6. Keep responses within six sentences.
7. Provide source references.

Example:

```text
Question:
"What is the annual leave policy?"
```

Response:

```text
Employees are entitled to 24 days of annual leave per year.
Unused leave can be carried forward according to the company policy.
```

Sources:

```text
HR_Handbook.pdf — Page 14
```

---

# 10. Handling Questions Outside the Sources

This is one of the core requirements of the application.

If a user asks:

> "Who is the current Prime Minister of India?"

but their uploaded documents contain no information about this topic, the system does not use the model's general knowledge.

Instead:

```text
I don't have the answer based on the provided documents.
```

The system uses retrieval evidence before generating an answer, reducing the likelihood of hallucinating unsupported information.

---

# 11. User Data Isolation

Each document belongs to a specific user.

```text
User A
 ├── document A
 ├── document B
 └── document C

User B
 ├── document X
 └── document Y
```

Retrieval is always scoped to the authenticated user's ID.

```text
JWT
 ↓
user_id
 ↓
retrieval filter
 ↓
only user's documents
```

This prevents one user from retrieving another user's documents.

The same user ID is maintained in:

- PostgreSQL
- S3 object paths
- Chroma metadata
- retrieval filtering

---

# API Endpoints

## Authentication

### Register

```http
POST /api/auth/register
```

Request:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2026-08-11T10:00:00Z"
}
```

---

### Login

```http
POST /api/auth/login
```

Request:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

---

### Current User

```http
GET /api/auth/me
```

Header:

```http
Authorization: Bearer <JWT>
```

---

# Document APIs

### Upload Document

```http
POST /api/documents
```

Content type:

```text
multipart/form-data
```

Form field:

```text
file
```

Supported:

```text
PDF
DOCX
TXT
```

Maximum active documents:

```text
5
```

---

### List Documents

```http
GET /api/documents
```

Returns the authenticated user's uploaded sources.

---

### Get Document

```http
GET /api/documents/{document_id}
```

The endpoint verifies that the requested document belongs to the authenticated user.

---

### Delete Document

```http
DELETE /api/documents/{document_id}
```

Deletion removes the document from:

```text
S3
 ↓
Vector store
 ↓
PostgreSQL
```

This prevents orphaned data from remaining in storage.

---

# Query API

### Ask a Question

```http
POST /api/query
```

Request:

```json
{
  "question": "What is the company's leave policy?"
}
```

Response:

```json
{
  "answer": "Employees are entitled to 24 days of annual leave per year.",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "HR_Handbook.pdf",
      "page": 14
    }
  ]
}
```

The query endpoint requires authentication.

Queries are only performed against documents belonging to the authenticated user.

---

# Database Design

PostgreSQL stores application metadata.

## Users

```text
users
├── id
├── email
├── password_hash
├── created_at
└── updated_at
```

## Documents

```text
documents
├── id
├── user_id
├── filename
├── file_type
├── file_size
├── s3_key
├── status
├── error_message
├── created_at
└── updated_at
```

Relationship:

```text
users
  │
  │ 1:N
  ▼
documents
```

The actual document content and vectors are not duplicated in PostgreSQL.

---

# Storage Architecture

## PostgreSQL

Used for:

- users
- authentication metadata
- document metadata
- document ownership
- processing status

## Amazon S3

Used for:

- original PDF files
- original DOCX files
- original TXT files

The bucket remains private.

When the frontend needs direct access to a private object, the backend can generate a temporary presigned URL.

## ChromaDB

Used for:

- document chunks
- embeddings
- retrieval metadata

---

# Project Structure

```text
backend/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── documents.py
│   │   └── query.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── document.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── document.py
│   │   └── query.py
│   │
│   ├── services/
│   │   └── s3_service.py
│   │
│   └── rag/
│       ├── __init__.py
│       ├── loaders.py
│       ├── chunking.py
│       ├── embeddings.py
│       ├── vector_store.py
│       ├── bm25.py
│       ├── hybrid_search.py
│       ├── reranker.py
│       ├── prompts.py
│       └── agent.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_documents.py
│   └── test_query.py
│
├── .env
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy

### Authentication

- JWT

### Database

- PostgreSQL(Neon)

### Object Storage

- Amazon S3

### RAG

- LangChain
- LangGraph
- ChromaDB
- BM25
- Reciprocal Rank Fusion
- Cross-encoder reranking

### Frontend

- React

### Testing

- pytest
- FastAPI TestClient

---

# Environment Variables

Create a `.env` file:

```env
APP_NAME=RAG Q&A Application
DEBUG=False

DATABASE_URL=postgresql+psycopg://username:password@host/database?sslmode=require

AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=your_region
AWS_BUCKET=your_bucket

JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

GOOGLE_API_KEY=your_google_api_key
```

Never commit `.env` or cloud credentials to version control.

---

# Installation

Clone the repository and enter the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

### Windows

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Run the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Running Tests

Run the complete test suite:

```bash
python -m pytest -v
```

Run authentication tests:

```bash
python -m pytest tests/test_auth.py -v
```

Run document tests:

```bash
python -m pytest tests/test_documents.py -v
```

Run query tests:

```bash
python -m pytest tests/test_query.py -v
```

---

# Design Principles

## Source Grounding

The model should answer from retrieved source material rather than relying on unsupported knowledge.

## User Isolation

Every retrieval operation is scoped to the authenticated user.

## Minimal Context

Only highly relevant, reranked chunks are sent to the LLM to reduce unnecessary token consumption.

## Transparent Answers

Answers contain references to the documents used to generate them.

## Simple Architecture

The application avoids unnecessary infrastructure and abstractions while maintaining clear separation between:

```text
API
Database
Storage
RAG
LLM
Frontend
```

---

# End-to-End Flow

The complete application flow is:

```text
                    USER
                      │
                      ▼
                 React Frontend
                      │
                      ▼
                 JWT Login
                      │
                      ▼
                   FastAPI
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
      Documents                 Query
          │                       │
          ▼                       ▼
         S3                 Hybrid Search
          │                       │
          ▼                       ▼
    Text Extraction           RRF Fusion
          │                       │
          ▼                       ▼
       Chunking               Reranking
          │                       │
          ▼                       ▼
      Embeddings             Evidence Gate
          │                       │
          ▼                       ▼
       ChromaDB                    LLM
                                  │
                                  ▼
                          Answer + Citations
                                  │
                                  ▼
                             React UI
```

---

# Future Improvements

The current architecture provides a strong foundation for further improvements, including:

- Background document ingestion
- Streaming LLM responses
- Conversation history
- Follow-up questions
- Query and retrieval evaluation
- Hybrid retrieval tuning
- Advanced metadata filtering
- Document preview
- Usage and token analytics
- Rate limiting
- Observability and tracing
- Production-grade asynchronous processing
- Automated RAG evaluation datasets

---

## Summary

**RAG Q&A** allows users to upload their own knowledge sources and interact with them conversationally while maintaining strict source grounding and user-level data isolation.

The system is designed to provide:

> **Relevant answers, minimal context, transparent citations, and no unsupported answers.**
