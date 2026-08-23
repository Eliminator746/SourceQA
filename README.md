# RAG Q&A — Conversational Source-Grounded Document Assistant

A full-stack **Conversational Retrieval-Augmented Generation (RAG)** application for asking questions over user-uploaded documents.

Users can upload up to **5 PDF, DOCX, or TXT files** and have multi-turn conversations grounded only in those sources. Follow-up questions such as **“What about its valuation?”** can use the previous conversation context without requiring the user to repeat the subject.

The system combines **hybrid retrieval, Reciprocal Rank Fusion (RRF), CrossEncoder reranking, a deterministic Evidence Gate, LangGraph agent memory, and metadata-based citations**.

> **Core rule:** if the uploaded documents do not contain sufficient evidence, the application does not answer from the model's general knowledge.

---

## Demo

![RAG Q&A frontend](docs/images/rag-qna-ui.png)

*Conversational document Q&A with inline citations and a document/source panel.*

---

## Features

- 🔐 JWT-based authentication
- 📄 PDF, DOCX, and TXT uploads
- 📚 Maximum of 5 active documents per user
- ☁️ Private Amazon S3 document storage
- 🗄️ PostgreSQL database hosted on Neon
- 💬 Multi-turn conversational Q&A
- 🧠 LangGraph agent with tool-calling and retrieval retry logic
- 💾 Conversation memory with LangGraph `InMemorySaver`
- 🔎 Hybrid retrieval:
  - ChromaDB semantic search
  - BM25 keyword search
  - Reciprocal Rank Fusion (RRF)
- 🎯 CrossEncoder reranking with `ms-marco-MiniLM-L-6-v2`
- 🛡️ Deterministic Evidence Gate
- 🤖 Gemini 3.6 Flash for grounded answer generation
- 📑 Inline `[1] [2] [3]` source citations
- 🔒 User-level document isolation
- 🚫 Refuses unsupported questions instead of using general knowledge
- 🧹 Document deletion across S3, ChromaDB, and PostgreSQL
- 🧪 Automated integration testing with pytest
- 📊 Offline LangSmith evaluation with LLM-as-judge metrics

---

## Architecture

```text
                         ┌──────────────────────┐
                         │      React UI        │
                         │                      │
                         │ Login                │
                         │ Documents            │
                         │ Conversation         │
                         │ Inline Citations     │
                         └──────────┬───────────┘
                                    │
                             HTTP + JWT
                         conversation_id
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │                      │
                         │ Auth API             │
                         │ Document API         │
                         │ Query API            │
                         └───────┬───────┬──────┘
                                 │       │
                   ┌─────────────┘       └──────────────┐
                   ▼                                    ▼
          ┌────────────────┐                   ┌────────────────┐
          │  PostgreSQL    │                   │   Amazon S3    │
          │    Neon DB     │                   │                │
          │                │                   │ Original files │
          │ Users          │                   │ PDF/DOCX/TXT   │
          │ Documents      │                   └────────────────┘
          │ Metadata       │
          └────────────────┘

                         ┌──────────────────────────────┐
                         │      LangGraph Agent         │
                         │                              │
                         │ Gemini 3.6 Flash             │
                         │ + search_documents tool      │
                         │ + InMemorySaver              │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                              Hybrid Retrieval
                             ┌─────────┴─────────┐
                             ▼                   ▼
                        ChromaDB               BM25
                       Semantic                 Keyword
                        Search                  Search
                             └─────────┬─────────┘
                                       ▼
                                   RRF Fusion
                                       ▼
                                 CrossEncoder
                                   Reranker
                                       ▼
                                 Evidence Gate
                                  /         \
                               FAIL         PASS
                                │             │
                           Retry /       Accepted
                           No Answer      Evidence
                                             │
                                             ▼
                                      Gemini 3.6 Flash
                                             │
                                             ▼
                                      Answer + Citations
```

---

## Document Ingestion Pipeline

```text
S3 Document
     ↓
Document Loader
(PDF / DOCX / TXT)
     ↓
LangChain Documents
     ↓
RecursiveCharacterTextSplitter
(chunk_size=800, overlap=120)
     ↓
Chunks + Metadata
(document_id, user_id, filename, page, chunk_index)
     ↓
Gemini Embeddings
     ↓
ChromaDB
```

For retrieval, BM25 is built over the authenticated user's chunks at query time.

---

## Query and Retrieval Pipeline

```text
User Question
      │
      ▼
LangGraph Agent
      │
      ▼
search_documents()
      │
      ├───────────────┐
      ▼               ▼
   ChromaDB          BM25
 Semantic Search   Keyword Search
      └───────┬───────┘
              ▼
         RRF Fusion
              ▼
       CrossEncoder
         Reranking
              ▼
       Top 5 Results
              ▼
        Evidence Gate
         score ≥ 0.30
           /     \
        FAIL     PASS
         │         │
     retry ≤3      ▼
               Accepted Evidence
                     │
                     ▼
                  Gemini
                     │
                     ▼
              Grounded Answer
                     │
                     ▼
                Citations
```

### Hybrid retrieval

- **Semantic search:** ChromaDB with Gemini embeddings
- **Keyword search:** BM25
- **Fusion:** LangChain `EnsembleRetriever` with RRF (`weights=[0.5, 0.5]`, `c=60`)
- **Reranking:** `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Final retrieval set:** top 5 reranked chunks

### Evidence Gate

The live Evidence Gate is deterministic:

```text
Best CrossEncoder score >= 0.30
        │
   ┌────┴────┐
   │         │
  PASS      FAIL
   │         │
   ▼         ▼
LLM       Retry retrieval
          up to 3 attempts
```

The gate is deliberately not an LLM call. It is a fast production-time relevance check. Offline quality evaluation is handled separately through LangSmith.

---

## Conversational RAG

Each conversation is identified by a UUID `conversation_id`.

The frontend sends the ID with follow-up questions:

```text
Turn 1
"What was Apple's stock performance in 2024?"
        ↓
Agent
        ↓
Answer
        ↓
conversation_id = ABC

Turn 2
"What about its valuation?"
        ↓
same conversation_id = ABC
        ↓
InMemorySaver restores conversation history
        ↓
Agent resolves "its" from context
        ↓
Retrieval + Evidence Gate
        ↓
Grounded Answer
```

No explicit query-rewriter is used in the current architecture. The agent receives the current question together with the conversation history.

> **Prototype limitation:** `InMemorySaver` stores state in process memory, so conversation history is lost when the backend restarts.

---

## Source Citations

Citations are generated from **retrieved evidence metadata**, not from the generated answer.

```text
Accepted Evidence
      ↓
document_id
filename
page
chunk_index
      ↓
Deduplicate by (document_id, page)
      ↓
Maximum 3 unique citations
      ↓
Frontend
```

The UI displays compact inline references such as:

```text
Apple's stock increased approximately 36% in 2024.[1]
```

This keeps source attribution deterministic and separate from LLM generation.

---

## Document Lifecycle

```text
Upload
  ↓
Validate file type + size
  ↓
Generate document UUID
  ↓
Store original in private S3
  ↓
Create PostgreSQL record
(status = processing)
  ↓
Background ingestion
  ↓
Extract → Chunk → Embed → ChromaDB
  ↓
status = ready
```

Supported states:

| Status | Meaning |
|---|---|
| `processing` | Document is being indexed |
| `ready` | Document is available for querying |
| `failed` | Ingestion failed |

A user can have at most **5 active documents**.

Deletion removes the document from:

```text
S3 → ChromaDB → PostgreSQL
```

---

## User Data Isolation

Isolation is enforced at each storage/retrieval layer:

```text
PostgreSQL
  → document ownership filtered by user_id

S3
  → documents/{user_id}/{document_id}.{extension}

ChromaDB
  → metadata filter: user_id

BM25
  → built only from the authenticated user's chunks
```

This prevents one user from retrieving another user's document content.

---

## API

### Authentication

```http
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### Documents

```http
POST   /api/documents
GET    /api/documents
GET    /api/documents/{document_id}
DELETE /api/documents/{document_id}
```

### Query

```http
POST /api/query
```

New conversation:

```json
{
  "question": "Which company had approximately a 36% stock increase in 2024?"
}
```

Continue conversation:

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
  "answer": "…",
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

---

## Evaluation

The project includes an offline LangSmith evaluation workflow with a small representative dataset.

The evaluation set covers:

- Answerable questions
- Unanswerable questions
- Multi-hop questions
- Paraphrased questions
- Citation-sensitive questions

Configured LLM-as-judge evaluators include:

- Retrieval relevance
- Groundedness
- Answer relevance
- Correctness

Because uploaded documents are user-defined, the evaluation dataset is used as a **representative regression suite**, not as a universal accuracy benchmark.

---

## Testing

The backend includes unit/integration coverage for:

- Document ingestion
- Document upload
- S3 → RAG ingestion
- RAG retrieval
- Query behavior
- Evidence Gate
- Evidence rejection
- Evidence deduplication
- Citation deduplication
- Query → citation integration
- Conversational request routing

Run the suite:

```bash
pytest -v tests/integration
```

The current integration baseline is **23 passing tests**.

---

## Project Structure

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
│   └── rag/
│       ├── agent.py
│       ├── retrieval.py
│       ├── ingestion.py
│       ├── loaders.py
│       ├── citations.py
│       └── evidence.py
├── evaluation/
│   ├── config.py
│   ├── dataset.py
│   ├── evaluators.py
│   ├── judge.py
│   ├── run_evaluation.py
│   └── target.py
├── tests/
│   ├── conftest.py
│   └── integration/
└── requirements.txt

frontend/
└── src/
    ├── api/
    │   ├── client.ts
    │   ├── auth.ts
    │   ├── documents.ts
    │   └── query.ts
    ├── context/
    │   └── AuthContext.tsx
    ├── hooks/
    │   ├── useAuth.ts
    │   ├── useConversation.ts
    │   ├── useDocuments.ts
    │   └── useQuery.ts
    ├── components/
    │   ├── LoginForm.tsx
    │   ├── RegisterForm.tsx
    │   ├── chat/
    │   │   ├── ChatPanel.tsx
    │   │   ├── AnswerCard.tsx
    │   │   ├── CitationList.tsx
    │   │   └── QuestionInput.tsx
    │   └── documents/
    │       ├── DocumentPanel.tsx
    │       ├── DocumentItem.tsx
    │       └── UploadDocument.tsx
    ├── pages/
    │   ├── ChatPage.tsx
    │   ├── LoginPage.tsx
    │   └── RegisterPage.tsx
    ├── routes/
    │   └── ProtectedRoute.tsx
    └── types/
```

---

## Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL / Neon

### Authentication

- JWT
- `pwdlib`

### Storage

- Amazon S3

### RAG

- LangChain
- LangGraph
- ChromaDB
- Gemini 3.6 Flash
- Gemini Embeddings
- BM25
- LangChain `EnsembleRetriever`
- RRF
- Sentence Transformers CrossEncoder

### Frontend

- React 19
- TypeScript
- Vite
- Axios
- React Router

### Evaluation & Testing

- LangSmith
- pytest
- FastAPI TestClient

---

## Environment Variables

Create `backend/.env`:

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

## Running Locally

### Backend

```bash
cd backend

python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Design Principles

### Source grounding
Answers should be supported by retrieved document evidence.

### User isolation
Every retrieval operation is scoped to the authenticated user.

### Minimal context
Only the top reranked evidence is passed to the LLM.

### Deterministic citations
Citations are built from evidence metadata rather than generated by the model.

### Clear separation of concerns

```text
React
  ↓
FastAPI
  ↓
Storage / Database
  ↓
RAG Retrieval
  ↓
Evidence Gate
  ↓
LLM
  ↓
Citations
```

---

## Known Limitations / Next Improvements

- Real token streaming is planned; the current UI returns the complete answer before rendering it.
- `InMemorySaver` loses conversation history after a backend restart.
- No document preview/page viewer yet.
- Retrieval weights and thresholds can be tuned further.
- Persistent conversation storage can be added for a production deployment.
- Rate limiting and usage/token analytics can be added later.

---

## Summary

**RAG Q&A** combines document ingestion, hybrid retrieval, reranking, deterministic evidence validation, conversational memory, and metadata-based citations into a single source-grounded assistant.

The goal is simple:

> **Retrieve the right evidence, answer only from that evidence, preserve conversational context, and show the user exactly where the answer came from.**
