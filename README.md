# RAG Q&A — Conversational Source-Grounded Document Assistant

A full-stack **Conversational** Retrieval-Augmented Generation (RAG) application that allows users to upload up to **5 documents** and have a multi-turn conversation based exclusively on the information contained within those sources. Users can ask follow-up questions, and the assistant resolves references from earlier in the conversation (e.g. "What about its valuation?" or "How does that compare?") without requiring the user to repeat context.

It includes a login feature so users can access their documents and continue conversations anytime. When the 5-document limit is reached, users can delete an existing document and upload a new one.

The system supports **PDF, DOCX, and TXT** files, performs **hybrid retrieval using semantic and keyword search**, reranks the retrieved results through a CrossEncoder, and generates concise answers with **source citations** for transparency.

If the requested information cannot be found in the user's uploaded sources, the application explicitly states that it does not have enough information to answer rather than relying on the model's general knowledge.

---

## Features

- 🔐 JWT-based user authentication
- 📄 Upload PDF, DOCX, and TXT documents
- 📚 Maximum of 5 active sources per user
- ☁️ Private document storage using Amazon S3
- 🗄️ PostgreSQL database hosted on Neon
- 💬 Multi-turn conversational Q&A with memory per session
- 🧠 LangGraph agent with tool-calling loop and retry logic
- 🔎 Hybrid retrieval using:
  - Semantic vector search (ChromaDB + Gemini embeddings)
  - BM25 keyword search
  - Reciprocal Rank Fusion (RRF)
- 🎯 Cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`)
- 🛡️ Evidence Gate — deterministic relevance threshold before answering
- 🤖 Source-grounded LLM responses (Gemini 3.6 Flash)
- 📑 Source/page citations with answers
- 🔒 User-level document isolation
- 🚫 Prevents answering from information outside the provided sources
- ⚡ Token-efficient context construction
- 🧹 Complete document deletion from S3, vector store, and database
- 🖥️ React frontend with live document status and conversation history
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
                         │  Conversation       │
                         └──────────┬──────────┘
                                    │
                         HTTP / JWT + conversation_id
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

                              ┌─────────────────────────────┐
                              │    LangGraph Agent          │
                              │                             │
                              │  conversation_id            │
                              │       ↓                     │
                              │  InMemorySaver              │
                              │  (thread memory)            │
                              │       ↓                     │
                              │  Gemini 3.6 Flash           │
                              │  + search_documents tool    │
                              └─────────────┬───────────────┘
                                            │
                                            ▼
                              ┌─────────────────────────────┐
                              │  search_documents tool      │
                              │  (up to 3 attempts)         │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              ▼              ▼              │
                   ┌──────────────┐  ┌──────────────┐      │
                   │   ChromaDB   │  │     BM25     │      │
                   │  Semantic    │  │   Keyword    │      │
                   │  Search      │  │   Search     │      │
                   └──────┬───────┘  └──────┬───────┘      │
                          │                 │               │
                          └────────┬────────┘               │
                                   ▼                        │
                          ┌──────────────────┐              │
                          │  EnsembleRetriever│             │
                          │  RRF Fusion       │             │
                          │  (weights 0.5/0.5)│             │
                          └────────┬─────────┘              │
                                   │                        │
                                   ▼                        │
                          ┌──────────────────┐              │
                          │  CrossEncoder    │              │
                          │  Reranker        │              │
                          │  (ms-marco-      │              │
                          │   MiniLM-L-6-v2) │              │
                          └────────┬─────────┘              │
                                   │                        │
                                   ▼                        │
                          ┌──────────────────┐              │
                          │  Evidence Gate   │              │
                          │                  │              │
                          │  score ≥ 0.30?   │              │
                          └───┬──────────────┘              │
                              │                             │
                    ┌─────────┴─────────┐                  │
                    ▼                   ▼                  │
                  FAIL               PASS                  │
                    │                   │                  │
                    ▼                   ▼                  │
               Retry ──────────────────────────────────────┘
               (up to 3×)           Context
                    │                   │
                    ▼                   ▼
               No Answer            Gemini LLM
                                        │
                                        ▼
                                  Answer + Citations
```

Document ingestion pipeline:

```text
S3 Document
     ↓
Document Loader (PDF/DOCX/TXT)
     ↓
Extracted LangChain Documents
     ↓
RecursiveCharacterTextSplitter
(chunk_size=800, overlap=120)
     ↓
Chunks with metadata
(document_id, user_id, filename, page, chunk_index)
     ↓
     ├──────────────────────┐
     ▼                      ▼
Gemini Embeddings        BM25 Index
(gemini-embedding-2)     (built at query time)
     │
     ▼
ChromaDB
```

---

# How It Works

## 1. Authentication

Users create an account and authenticate using JWT.

```text
Register
   ↓
Password hashing (pwdlib)
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
Client stores token in localStorage
```

The JWT is required for all protected document and query endpoints.

Every request is associated with the authenticated user's ID, ensuring complete data isolation.

---

## 2. Document Upload

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
Validate file size (≤ 10 MB)
 ↓
Validate actual MIME type (python-magic)
 ↓
Generate document UUID
 ↓
Upload original file to private S3
 ↓
Create PostgreSQL document record (status: processing)
 ↓
Background ingestion task
 ↓
PostgreSQL status updated (ready / failed)
```

S3 objects use a user-scoped structure:

```text
documents/{user_id}/{document_id}.{extension}
```

The frontend polls for document status every 3 seconds while any document is in `processing` state, and automatically unlocks the question input once at least one document reaches `ready`.

---

## 3. Document Processing

Once a document is uploaded, the ingestion pipeline extracts and indexes its content.

```text
S3 Document
     ↓
Document Loader (PDF → PyPDFLoader, DOCX → python-docx, TXT → decode)
     ↓
Extracted LangChain Documents
     ↓
RecursiveCharacterTextSplitter
(chunk_size=800, overlap=120)
     ↓
Chunks with metadata
```

Each chunk carries:

```json
{
  "document_id": "document-uuid",
  "user_id": "user-uuid",
  "filename": "Stock_Market_Performance_2024.pdf",
  "file_type": "pdf",
  "page": 2,
  "chunk_index": 7
}
```

For **PDF**, pages are preserved so citations can reference the exact page.
For **DOCX**, paragraph index is stored.
For **TXT**, the full text is treated as a single document.

Chunks are stored in ChromaDB with deterministic IDs (`{document_id}_chunk_{chunk_index}`), which allows safe re-ingestion without duplication.

---

## 4. Hybrid Retrieval

At query time, the system retrieves candidate chunks using two independent methods:

```text
Question
    │
    ├──────────────────────────────────┐
    ▼                                  ▼
ChromaDB                            BM25Retriever
Semantic Search                     Keyword Search
(cosine similarity,                 (built from all user
 top 20)                             chunks, top 20)
    │                                  │
    └────────────────┬─────────────────┘
                     ▼
              EnsembleRetriever
              RRF Fusion
              (weights=[0.5, 0.5], c=60)
                     │
                     ▼
              Unified ranked candidates
```

Semantic search captures conceptual relevance. BM25 captures exact keyword matches (product names, error codes, specific terms). RRF combines both rankings into a single ordered list without requiring score normalization.

---

## 5. Cross-Encoder Reranking

The top hybrid candidates are passed through a cross-encoder:

```text
Hybrid candidates (up to 40)
         ↓
CrossEncoder (ms-marco-MiniLM-L-6-v2)
         ↓
Score each (question, chunk) pair
         ↓
Sort by relevance score (descending)
         ↓
Top 5 reranked results
```

The cross-encoder reads the question and the chunk together, giving more precise relevance judgements than bi-encoder (vector) similarity alone.

---

## 6. Evidence Gate

Before the retrieved chunks reach the LLM, they pass through a deterministic relevance gate:

```text
Reranked results
       ↓
Best CrossEncoder score ≥ 0.30?
       │
   ┌───┴───┐
   NO      YES
   │        │
   ▼        ▼
Retry     Accept evidence
(up to     ↓
 3×)    Pass to LLM
```

The gate checks that at least one chunk has a relevance score at or above the threshold. If not, the search tool returns `NO_RELEVANT_INFORMATION` and the agent can reformulate and retry.

This gate is intentionally **not** LLM-based — it is a fast deterministic check that prevents irrelevant chunks from reaching the model.

---

## 7. Conversational Agent

The core of the system is a LangGraph agent that handles multi-turn conversations.

```text
User question
      ↓
LangGraph Agent (Gemini 3.6 Flash)
      │
      │  Sees:
      │  - Current question
      │  - Full conversation history (via InMemorySaver)
      │
      ▼
search_documents tool
      ↓
Hybrid Retrieval → RRF → CrossEncoder → Evidence Gate
      │
  ┌───┴────┐
FAIL      PASS
  │         │
  ▼         ▼
Retry    Context string
(≤3×)       │
  │         ▼
  │    Gemini 3.6 Flash
  │    (grounded answer)
  │         │
  ▼         ▼
No Answer  Answer + metadata
           for citation building
```

**Conversation memory** is handled by LangGraph's `InMemorySaver` checkpointer. Each conversation is identified by a `conversation_id` (UUID). All requests sharing the same `conversation_id` use the same conversation thread.

This allows the agent to resolve follow-up references without an explicit query rewriter:

```text
Turn 1: "Which company had approximately a 36% stock increase in 2024?"
Turn 2: "What was driving that growth?"       ← "that" resolved from history
Turn 3: "How does it compare to its peers?"   ← "it" resolved from history
```

> **Note:** `InMemorySaver` stores history in process memory. Conversation history is lost if the server restarts.

The `conversation_id` is returned with every query response. The frontend stores it and passes it with every subsequent question in the same session. Clearing the conversation in the UI discards the ID, starting a fresh thread.

---

## 8. Source-Grounded Answer Generation

The accepted evidence chunks are formatted and passed to Gemini 3.6 Flash as context.

The agent's system prompt instructs the model to:

1. Use **only** the `search_documents` tool output as factual evidence.
2. Never use general knowledge to answer.
3. Use conversation history **only** to understand the current question, never as evidence.
4. Retry up to 3 times if sufficient evidence is not found.
5. Respond with exactly `"I don't have the answer based on the provided documents."` if evidence cannot be found after all attempts.
6. Keep answers concise: maximum 6 sentences, preferably 2–4.
7. Never expose internal scores, metadata, or implementation details.

---

## 9. Citation Building

Citations are built from chunk metadata — **not** extracted from the LLM response.

```text
Accepted evidence (document, score) pairs
        ↓
Extract: document_id, filename, page (normalized to 1-based), chunk_index
        ↓
Deduplicate by (document_id, page)
        ↓
Max 3 citations
        ↓
Return to frontend
```

If multiple chunks from the same page are retrieved, only one citation for that page is returned.

---

## 10. Handling Questions Outside the Sources

If a user asks a question whose answer is not in any uploaded document:

```text
Agent calls search_documents
        ↓
Hybrid retrieval finds candidates
        ↓
Evidence Gate: best score < 0.30
        ↓
Returns NO_RELEVANT_INFORMATION
        ↓
Agent reformulates and retries (up to 3×)
        ↓
Still no evidence found
        ↓
"I don't have the answer based on the provided documents."
```

The system does not fall back to the LLM's general knowledge.

---

## 11. User Data Isolation

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

Isolation is enforced at every layer:

- **PostgreSQL** — queries filter by `user_id`
- **S3** — objects are stored under `documents/{user_id}/`
- **ChromaDB** — semantic retrieval uses `filter: { "user_id": user_id }`
- **BM25** — built from only the authenticated user's chunks

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

Response (`201 Created`):

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

Supported formats:

```text
PDF · DOCX · TXT
```

Maximum active documents per user:

```text
5
```

Response (`201 Created`):

```json
{
  "message": "Document uploaded and is being indexed",
  "document_id": "uuid",
  "filename": "report.pdf",
  "status": "processing"
}
```

---

### List Documents

```http
GET /api/documents
```

Returns the authenticated user's uploaded sources.

Response:

```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "report.pdf",
      "file_type": "pdf",
      "file_size": 204800,
      "status": "ready",
      "created_at": "2026-08-11T10:00:00Z"
    }
  ],
  "count": 1,
  "max_sources": 5
}
```

Document `status` values:

| Value        | Meaning                           |
| ------------ | --------------------------------- |
| `processing` | Background ingestion is running   |
| `ready`      | Indexed and available for queries |
| `failed`     | Ingestion failed                  |

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
S3 → ChromaDB (vector chunks) → PostgreSQL
```

---

# Query API

### Ask a Question

```http
POST /api/query
```

**New conversation** (omit `conversation_id`):

```json
{
  "question": "Which company had approximately a 36% stock increase in 2024?"
}
```

**Continuing a conversation** (include `conversation_id` from the previous response):

```json
{
  "question": "What was driving that growth?",
  "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

Response:

```json
{
  "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "answer": "According to the document Stock_Market_Performance_2024.pdf, both Apple and Alphabet had stock price increases of approximately 36% in 2024.",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "Stock_Market_Performance_2024.pdf",
      "page": 3,
      "chunk_index": 12
    }
  ]
}
```

The `conversation_id` in the response must be passed back with subsequent questions to maintain conversation context. Omitting it starts a new conversation thread.

---

# Database Design

PostgreSQL stores application metadata only. Document content and vectors are stored separately.

## Users

```text
users
├── id             UUID
├── email          unique
├── password_hash
├── created_at
└── updated_at
```

## Documents

```text
documents
├── id             UUID
├── user_id        FK → users.id
├── filename
├── file_type      pdf | docx | txt
├── file_size      bytes
├── s3_key
├── status         processing | ready | failed
├── error_message  populated on failure
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

---

# Storage Architecture

## PostgreSQL

Used for:

- users and authentication metadata
- document ownership and metadata
- document processing status

## Amazon S3

Used for original uploaded files (PDF, DOCX, TXT). The bucket is private.

## ChromaDB

Used for:

- document chunk text
- Gemini embedding vectors
- retrieval metadata (document_id, user_id, filename, page, chunk_index)

## Conversation Memory

LangGraph `InMemorySaver` stores conversation history per `thread_id` (= `conversation_id`).

> This is process-level memory. History is lost on server restart.

---

# Project Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   └── query.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/
│   │   ├── user.py
│   │   └── document.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── document.py
│   │   └── query.py
│   ├── services/
│   │   ├── s3_service.py
│   │   ├── rag_ingestion.py
│   │   └── auth_service.py
│   └── rag/
│       ├── agent.py          ← LangGraph conversational agent
│       ├── retrieval.py      ← Hybrid search + CrossEncoder reranker
│       ├── ingestion.py      ← Chunking + ChromaDB
│       ├── loaders.py        ← PDF / DOCX / TXT loaders
│       ├── citations.py      ← Citation builder
│       └── evidence.py       ← Evidence Gate
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_documents.py
│   ├── test_query.py
│   ├── test_citations.py
│   ├── test_evidence.py
│   └── integration/
│       ├── test_document_ingestion.py
│       ├── test_document_upload.py
│       ├── test_rag_query.py
│       └── test_s3_rag_ingestion.py
├── evaluation/
│   ├── config.py
│   ├── dataset.py
│   ├── evaluators.py
│   ├── judge.py
│   ├── run_evaluation.py
│   └── target.py
└── requirements.txt

frontend/
├── src/
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts         ← Axios + JWT interceptor
│   │   ├── auth.ts
│   │   ├── documents.ts
│   │   └── query.ts
│   ├── context/
│   │   └── AuthContext.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useConversation.ts ← Tracks conversation_id + message history
│   │   ├── useDocuments.ts    ← Polls status while processing
│   │   └── useQuery.ts
│   ├── components/
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── AnswerCard.tsx
│   │   │   ├── CitationList.tsx
│   │   │   └── QuestionInput.tsx
│   │   └── documents/
│   │       ├── DocumentPanel.tsx
│   │       ├── DocumentItem.tsx  ← Shows indexing status
│   │       └── UploadDocument.tsx
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   ├── LoginPage.tsx
│   │   └── RegisterPage.tsx
│   ├── routes/
│   │   └── ProtectedRoute.tsx
│   └── types/
│       ├── auth.ts
│       ├── chat.ts
│       ├── document.ts
│       └── query.ts           ← Includes conversation_id in request/response
└── package.json
```

---

# Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy

### Authentication

- JWT (python-jose / PyJWT)
- pwdlib (password hashing)

### Database

- PostgreSQL (Neon)

### Object Storage

- Amazon S3

### RAG & Conversation

- LangChain
- LangGraph (conversational agent + InMemorySaver)
- Gemini 3.6 Flash (LLM)
- gemini-embedding-2 (embeddings)
- ChromaDB (vector store)
- BM25 (keyword retrieval)
- LangChain EnsembleRetriever + RRF
- CrossEncoder `ms-marco-MiniLM-L-6-v2` (reranking)
- Deterministic Evidence Gate (relevance threshold)

### Frontend

- React 19 + TypeScript
- Vite
- Axios
- React Router

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

```text
                    USER
                      │
                      ▼
                 React Frontend
                 (Conversation UI)
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
      Documents               Query
          │                  question +
          ▼                  conversation_id
         S3                       │
          │                       ▼
          ▼               LangGraph Agent
    Text Extraction       (Gemini 3.6 Flash)
          │                       │
          ▼               search_documents
       Chunking           tool (≤3 retries)
          │                       │
          ▼                       ▼
      Gemini            Hybrid Search (Chroma + BM25)
      Embeddings                  │
          │                       ▼
          ▼                     RRF Fusion
       ChromaDB                   │
                                  ▼
                             CrossEncoder
                                  │
                                  ▼
                            Evidence Gate
                                  │
                    ┌─────────────┴──────────────┐
                    ▼                            ▼
               No evidence                  Evidence
               → retry / no answer          accepted
                                                │
                                                ▼
                                           Gemini LLM
                                           (grounded)
                                                │
                                                ▼
                                    Answer + conversation_id
                                    + Citations (from metadata)
                                                │
                                                ▼
                              React UI (stored conversation_id
                              sent with next question)
```

---

# Future Improvements

- Persistent conversation history (database-backed, survives server restart)
- Streaming LLM responses
- Document preview / page viewer
- Query and retrieval evaluation dashboard
- Hybrid retrieval tuning (weight adjustment per query type)
- Advanced metadata filtering (by document, date range, file type)
- Usage and token analytics
- Rate limiting
- Observability and tracing (LangSmith)
- Production-grade async document ingestion queue
- Automated RAG evaluation datasets

---

## Summary

**RAG Q&A** allows users to upload their own knowledge sources and have a **multi-turn conversation** with them, maintaining strict source grounding and user-level data isolation.

The system is designed to provide:

> **Relevant answers from a conversational agent, minimal context, transparent citations, and no unsupported answers.**
