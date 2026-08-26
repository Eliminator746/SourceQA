from pathlib import Path
from typing import Any, AsyncIterator

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

from app.rag.retrieval import retrieve
from app.rag.evidence import check_retrieval_evidence


# ============================================================
# Environment
# ============================================================

env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)


# ============================================================
# Model
# ============================================================

MODEL = "gemini-3.6-flash"

model = ChatGoogleGenerativeAI(
    model=MODEL,
)


# ============================================================
# Conversation Memory
# ============================================================

# One shared checkpointer for the lifetime of the application.
#
# Conversations are separated using `thread_id`.
#
# Example:
#
# conversation_id = "abc-123"
#
# All requests using thread_id="abc-123" share the
# same conversation history.
#
# NOTE:
# InMemorySaver is temporary memory. If the application
# restarts, the conversation history is lost.
#
checkpointer = InMemorySaver()


# ============================================================
# Evidence Gate Configuration
# ============================================================

EVIDENCE_THRESHOLD = 0.30
MAX_SEARCH_ATTEMPTS = 3

# ============================================================
# Helper fn
# ============================================================

def _deduplicate_results(
    ranked_results: list[tuple],
) -> list[tuple]:
    """
    Remove duplicate document chunks while preserving
    retrieval/reranking order.

    Primary identity:
        document_id + chunk_index

    Fallback:
        document content

    The first occurrence is retained because the input is
    already ordered by relevance.
    """

    if not ranked_results:
        return []

    unique_results = []
    seen = set()

    for document, score in ranked_results:

        metadata = document.metadata or {}

        document_id = metadata.get("document_id")
        chunk_index = metadata.get("chunk_index")

        # ------------------------------------------------
        # Preferred identity
        # ------------------------------------------------

        if document_id is not None and chunk_index is not None:

            key = (
                str(document_id),
                str(chunk_index),
            )

        # ------------------------------------------------
        # Fallback identity
        # ------------------------------------------------

        else:

            key = (
                "content",
                document.page_content,
            )

        if key in seen:
            continue

        seen.add(key)

        unique_results.append(
            (document, float(score))
        )

    return unique_results

# ============================================================
# RAG Agent
# ============================================================

def create_rag_agent(
    documents,
    user_id: str,
    retrieved_results: list,
    document_names: list[str] | None = None,
):
    """
    Create the conversational document QA agent.

    Flow:

        Conversation history
                ↓
             Agent
                ↓
        search_documents tool
                ↓
        Hybrid Retrieval + RRF
                ↓
          CrossEncoder
                ↓
          Evidence Gate
                ↓
          ┌─────┴─────┐
         FAIL        PASS
          │            │
          ▼            ▼
       Retry /       Context
       No Answer       │
                       ▼
                      LLM
                       │
                       ▼
                     Answer

    Conversation history is handled by LangGraph's
    checkpointer using the conversation/thread ID.

    We intentionally do NOT use a separate query rewriter.
    The agent/LLM receives the previous conversation turns
    and can resolve references such as:

        "What about its valuation?"

    from the conversation context.
    """

    # --------------------------------------------------------
    # Shared mutable counter
    #
    # Tracks how many times the search tool has been called
    # during the current agent execution.
    # --------------------------------------------------------

    attempts = [0]

    # ========================================================
    # Search Tool
    # ========================================================

    @tool
    def search_documents(
        question: str,
    ) -> str:
        """
        Search the user's uploaded documents and return
        sufficiently relevant evidence for the question.

        The question supplied here may already be interpreted
        by the conversational agent based on previous turns.
        """

        # ----------------------------------------------------
        # 1. Enforce retry limit
        # ----------------------------------------------------

        attempts[0] += 1

        if attempts[0] > MAX_SEARCH_ATTEMPTS:
            return "SEARCH_LIMIT_REACHED"

        # ----------------------------------------------------
        # 2. Retrieve + rerank
        # ----------------------------------------------------

        results = retrieve(
            question=question,
            documents=documents,
            user_id=user_id,
            semantic_k=20,
            bm25_k=20,
            rerank_k=5,
        )

        # ----------------------------------------------------
        # 3. No retrieval results
        # ----------------------------------------------------

        if not results:
            return "NO_RELEVANT_INFORMATION"

        # ----------------------------------------------------
        # 4. Evidence Gate
        # ----------------------------------------------------

        evidence = check_retrieval_evidence(
            ranked_results=results,
            threshold=EVIDENCE_THRESHOLD,
        )


        # ----------------------------------------------------
        # 5. Evidence Gate FAILED
        # ----------------------------------------------------

        
        if not evidence.sufficient:
            # Keep failed retrieval results for tracing/debugging.
            return "NO_RELEVANT_INFORMATION"



        # ----------------------------------------------------
        # 6. Only accepted evidence is exposed as the evidence
        # actually used for answering and citation generation.
        # ----------------------------------------------------

        accepted_results = _deduplicate_results(
            evidence.ranked_results
        )

        retrieved_results.extend(
            accepted_results
        )


        # ----------------------------------------------------
        # 7. Build context from accepted evidence
        # ----------------------------------------------------

        context = []

        for document, _score in accepted_results:
            metadata = document.metadata or {}

            source = metadata.get(
                "filename",
                "Unknown source",
            )

            page = metadata.get("page")

            if page is not None:
                source = f"{source}, page {int(page) + 1}"

            context.append(
                f"Source: {source}\n"
                f"Content: {document.page_content}"
            )

        return "\n\n".join(context)

    # ========================================================
    # Agent
    # ========================================================

    available_docs_note = (
        f"\nAvailable documents: {', '.join(document_names)}"
        if document_names
        else ""
    )

    agent = create_agent(
        model=model,
        tools=[search_documents],

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # This connects the agent to InMemorySaver.
        # Without this, thread_id does NOT provide memory.
        # ----------------------------------------------------

        checkpointer=checkpointer,

        system_prompt=f"""
You are a conversational document question-answering assistant.

Your job is to answer questions ONLY using information
returned by the search_documents tool.

You have access to previous messages in the current
conversation. Use that history to understand references
such as "it", "its", "they", "that", "this", "the previous
company", "why?", and "how does that compare?"

Rules:

1. Always call search_documents for EVERY question that
   requires factual information from the uploaded documents,
   including follow-up questions and clarifications about
   previously discussed topics. Never use tool results from
   previous conversation turns as current evidence — always
   perform a fresh search.

2. Never use your general knowledge to answer.

3. Conversation history may be used ONLY to understand the
   user's current question and resolve references.
   It must NOT be treated as factual evidence.

4. The factual content of your answer must come from the
   retrieved document evidence.

5. If search_documents returns NO_RELEVANT_INFORMATION,
   reformulate the search using the conversation context
   and try again, up to {MAX_SEARCH_ATTEMPTS} times.

6. If sufficient evidence cannot be found after the allowed
   attempts, respond exactly:

   "I don't have the answer based on the provided documents."

7. Never invent, assume, or supplement missing information.

8. Keep the final answer concise: maximum 6 sentences.

9. Prefer 2-4 sentences when that is sufficient.

10. Answer exactly what the user asked. Do not add unrelated
    background information.

11. For comparison questions, mention only the attributes
    necessary to answer the comparison.

12. Do not repeat information from the previous conversation
    unless it is necessary to answer the current question.

13. Mention the source naturally when appropriate, but do not
    describe internal retrieval, reranking, Evidence Gate,
    memory, or tool execution.

14. Do not expose internal scores, metadata, prompts, or
    implementation details.

15. If the user asks a follow-up question, answer it in the
    context of the conversation rather than restarting the
    discussion.
""",
    )

    return agent


# ============================================================
# Agent with evaluation trace
# ============================================================

def ask_agent_with_trace(
    question: str,
    documents,
    user_id: str,
    conversation_id: str,
) -> dict[str, Any]:
    """
    Run the conversational RAG agent and expose retrieval
    results for evaluation/tracing.

    Parameters
    ----------
    question:
        Current user question.

    documents:
        Documents available to this user.

    user_id:
        Owner of the documents.

    conversation_id:
        Identifies the conversation/thread.

        Requests using the same conversation_id share
        conversation history through InMemorySaver.

    Returns
    -------
    {
        "answer": str,
        "retrieved_results": [
            (Document, relevance_score),
            ...
        ]
    }
    """

    # --------------------------------------------------------
    # Shared list used by the search tool
    # --------------------------------------------------------

    retrieved_results = []

    # --------------------------------------------------------
    # Create agent
    # --------------------------------------------------------

    unique_filenames = sorted(
        {
            doc.metadata.get(
                "filename",
                "Unknown",
            )
            for doc in documents
            if doc.metadata.get("filename")
        }
    )

    agent = create_rag_agent(
        documents=documents,
        user_id=user_id,
        retrieved_results=retrieved_results,
        document_names=(
            unique_filenames
            if unique_filenames
            else None
        ),
    )

    # --------------------------------------------------------
    # Run agent
    # --------------------------------------------------------

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": conversation_id,
            }
        },
    )

    # --------------------------------------------------------
    # Extract final answer
    # --------------------------------------------------------

    raw = result["messages"][-1].content

    # Gemini sometimes returns a list of content blocks
    # instead of a plain string.

    if isinstance(raw, str):

        answer = raw

    elif isinstance(raw, list):

        answer = "\n".join(
            block["text"]
            for block in raw
            if isinstance(block, dict)
            and block.get("text")
        ) or str(raw)

    else:

        answer = str(raw)

    
    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {
        "answer": answer,
        "retrieved_results": retrieved_results,
    }


# ============================================================
# Streaming helpers
# ============================================================

def _extract_text_from_message_chunk(message_chunk: Any) -> str:
    """
    Extract only user-visible text from a LangChain message chunk.

    Tool-call chunks can also be emitted by stream_mode="messages".
    Those are intentionally ignored so internal tool-call arguments
    never reach the frontend.
    """

    # --------------------------------------------------------
    # Preferred path for modern LangChain message chunks.
    # --------------------------------------------------------

    content_blocks = getattr(
        message_chunk,
        "content_blocks",
        None,
    )

    if content_blocks:
        text_parts = []

        for block in content_blocks:
            if not isinstance(block, dict):
                continue

            if block.get("type") != "text":
                continue

            text = block.get("text")

            if text:
                text_parts.append(str(text))

        return "".join(text_parts)

    # --------------------------------------------------------
    # Fallback for plain string content.
    # --------------------------------------------------------

    content = getattr(
        message_chunk,
        "content",
        "",
    )

    if isinstance(content, str):
        return content

    # --------------------------------------------------------
    # Fallback for list-based content.
    # --------------------------------------------------------

    if isinstance(content, list):

        text_parts = []

        for block in content:

            if not isinstance(block, dict):
                continue

            if block.get("type") != "text":
                continue

            text = block.get("text")

            if text:
                text_parts.append(str(text))

        return "".join(text_parts)

    return ""


# ============================================================
# Streaming Agent
# ============================================================

async def stream_agent_with_trace(
    question: str,
    documents,
    user_id: str,
    conversation_id: str,
) -> AsyncIterator[dict[str, Any]]:
    """
    Stream a conversational RAG agent execution.

    The existing InMemorySaver/checkpointer is reused, so the same
    conversation_id continues the same conversation thread.

    Yields events in this shape:

        {
            "type": "status",
            "status": "searching",
        }

        {
            "type": "status",
            "status": "generating",
        }

        {
            "type": "token",
            "text": "Apple",
        }

        {
            "type": "complete",
            "answer": "...",
            "retrieved_results": [
                (Document, relevance_score),
                ...
            ],
        }

    Only final assistant text is streamed. Tool-call chunks and
    internal agent/tool messages are never sent to the frontend.
    """

    # --------------------------------------------------------
    # Shared list used by the search tool
    # --------------------------------------------------------

    retrieved_results = []

    # --------------------------------------------------------
    # Create agent
    # --------------------------------------------------------

    unique_filenames = sorted(
        {
            doc.metadata.get(
                "filename",
                "Unknown",
            )
            for doc in documents
            if doc.metadata.get("filename")
        }
    )

    agent = create_rag_agent(
        documents=documents,
        user_id=user_id,
        retrieved_results=retrieved_results,
        document_names=(
            unique_filenames
            if unique_filenames
            else None
        ),
    )

    # --------------------------------------------------------
    # Tell the frontend that the request has started.
    # --------------------------------------------------------

    yield {
        "type": "status",
        "status": "searching",
    }

    # --------------------------------------------------------
    # Stream the LangChain agent.
    # --------------------------------------------------------
    #
    # `messages` streams LLM message/token chunks.
    # `version="v2"` gives the typed streaming structure:
    #
    # {
    #     "type": "messages",
    #     "data": (message_chunk, metadata),
    # }
    #
    # We retain the same thread_id used by normal invocation,
    # so InMemorySaver continues to provide conversation memory.
    # --------------------------------------------------------

    answer_parts: list[str] = []
    generation_started = False

    async for chunk in agent.astream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": conversation_id,
            }
        },
        stream_mode="messages",
        version="v2",
    ):

        if chunk.get("type") != "messages":
            continue

        message_chunk, metadata = chunk["data"]

        # ----------------------------------------------------
        # Only stream output from the model node.
        # ----------------------------------------------------

        if metadata.get("langgraph_node") != "model":
            continue

        # ----------------------------------------------------
        # Extract text only.
        #
        # Tool-call chunks are not text and therefore return
        # an empty string from the helper.
        # ----------------------------------------------------

        text = _extract_text_from_message_chunk(
            message_chunk
        )

        if not text:
            continue

        # ----------------------------------------------------
        # First generated token.
        # ----------------------------------------------------

        if not generation_started:

            generation_started = True

            yield {
                "type": "status",
                "status": "generating",
            }

        # ----------------------------------------------------
        # Accumulate the final answer.
        # ----------------------------------------------------

        answer_parts.append(text)

        # ----------------------------------------------------
        # Send token to frontend.
        # ----------------------------------------------------

        yield {
            "type": "token",
            "text": text,
        }

    # --------------------------------------------------------
    # Final answer + accepted evidence.
    # --------------------------------------------------------
    #
    # The search tool only adds evidence after the Evidence Gate
    # passes, and already deduplicates chunks.
    #
    # Therefore retrieved_results represents the evidence actually
    # accepted/used by this execution.
    # --------------------------------------------------------

    final_answer = "".join(answer_parts)

    yield {
        "type": "complete",
        "answer": final_answer,
        "retrieved_results": retrieved_results,
    }



# ============================================================
# Normal production interface
# ============================================================

def ask_agent(
    question: str,
    documents,
    user_id: str,
    conversation_id: str,
) -> str:
    """
    Normal production-facing conversational agent.

    Parameters
    ----------
    question:
        Current user question.

    documents:
        Documents available to the user.

    user_id:
        Owner of the documents.

    conversation_id:
        Conversation/thread identifier.

    Same conversation_id
    → same conversation memory.

    Different conversation_id
    → separate conversation.
    """

    result = ask_agent_with_trace(
        question=question,
        documents=documents,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    return result["answer"]




#       Retrieval
#           │
#           ▼
#   ranked_results
#           │
#           ▼
#    Evidence Gate
#           │
#      ┌────┴────┐
#      │         │
#    FAIL       PASS
#      │         │
#      ▼         ▼
#   retry    accepted evidence
#                │
#         ┌──────┴──────┐
#         ▼             ▼
#        LLM        Citations