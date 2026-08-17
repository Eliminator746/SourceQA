from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from app.rag.retrieval import retrieve


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
    model=MODEL
)


# ============================================================
# RAG Agent
# ============================================================

def create_rag_agent(
    documents,
    user_id: str,
    retrieved_results: list,
):
    """
    Create the document QA agent.

    `retrieved_results` is a mutable list shared with the
    search tool so that the evaluation layer can inspect the
    actual evidence retrieved during the agent execution.
    """

    @tool
    def search_documents(
        question: str,
    ) -> str:
        """
        Search the user's uploaded documents and return
        the most relevant information for the question.
        """

        results = retrieve(
            question=question,
            documents=documents,
            user_id=user_id,
            semantic_k=20,
            bm25_k=20,
            rerank_k=5,
        )

        if not results:
            return "NO_RELEVANT_INFORMATION"

        # ----------------------------------------------------
        # Capture the actual retrieval results
        # ----------------------------------------------------
        #
        # retrieve() currently returns:
        #
        # [
        #     (Document, relevance_score),
        #     ...
        # ]
        #
        # We keep those objects for LangSmith evaluation.
        #

        retrieved_results.extend(results)

        # ----------------------------------------------------
        # Build context for the agent
        # ----------------------------------------------------

        context = []

        for document, score in results:

            metadata = document.metadata or {}

            source = metadata.get(
                "filename",
                "Unknown source",
            )

            page = metadata.get("page")

            if page is not None:
                source = f"{source}, page {page + 1}"

            context.append(
                f"Source: {source}\n"
                f"Content: {document.page_content}"
            )

        return "\n\n".join(context)

    # ========================================================
    # Agent
    # ========================================================

    agent = create_agent(
        model=model,
        tools=[search_documents],
        system_prompt="""
You are a document question-answering assistant.

Your job is to answer questions ONLY using information
returned by the search_documents tool.

Rules:

1. Always use the search_documents tool for questions
   about the user's uploaded documents.

2. Do not use your general knowledge to answer.

3. If the tool returns NO_RELEVANT_INFORMATION,
   say exactly:
   "I don't have the answer based on the provided documents."

4. Do not invent or assume information.

5. Keep the answer concise and within 6 sentences.

6. Mention the source when answering.

7. If the retrieved information does not sufficiently
   answer the question, say that you don't have enough
   information rather than guessing.
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
) -> dict[str, Any]:
    """
    Run the RAG agent and expose the retrieval results.

    This function is primarily useful for LangSmith evaluation.

    Returns:

        {
            "answer": str,
            "retrieved_results": [
                (Document, relevance_score),
                ...
            ]
        }

    The retrieved results are the actual results produced by
    the hybrid retrieval + RRF + CrossEncoder pipeline.
    """

    # --------------------------------------------------------
    # Shared list used by the search tool
    # --------------------------------------------------------

    retrieved_results = []

    # --------------------------------------------------------
    # Create agent
    # --------------------------------------------------------

    agent = create_rag_agent(
        documents=documents,
        user_id=user_id,
        retrieved_results=retrieved_results,
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
        }
    )

    # --------------------------------------------------------
    # Extract final answer
    # --------------------------------------------------------

    answer = result["messages"][-1].content

    # --------------------------------------------------------
    # Remove duplicate chunks if the agent searched more
    # than once during the same question.
    # --------------------------------------------------------

    unique_results = []
    seen = set()

    for document, score in retrieved_results:

        metadata = document.metadata or {}

        key = (
            metadata.get("document_id"),
            metadata.get("chunk_index"),
        )

        # If metadata doesn't contain enough information to
        # identify the chunk, fall back to its content.
        if key == (None, None):
            key = document.page_content

        if key in seen:
            continue

        seen.add(key)

        unique_results.append(
            (document, score)
        )

    return {
        "answer": answer,
        "retrieved_results": unique_results,
    }


# ============================================================
# Normal production interface
# ============================================================

def ask_agent(
    question: str,
    documents,
    user_id: str,
) -> str:
    """
    Normal production-facing agent function.

    Keeps the original contract:

        question + documents + user_id
                    ↓
                 string
    """

    result = ask_agent_with_trace(
        question=question,
        documents=documents,
        user_id=user_id,
    )

    return result["answer"]