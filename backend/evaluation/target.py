from app.rag.ingestion import get_user_chunks
from app.rag.agent import ask_agent_with_trace

from evaluation.config import EVAL_USER_ID

def extract_answer_text(answer) -> str:
    """
    Normalize LangChain/Gemini content into a plain string.
    """

    if isinstance(answer, str):
        return answer

    if isinstance(answer, list):
        text_parts = []

        for block in answer:
            if isinstance(block, dict):
                text = block.get("text")

                if text:
                    text_parts.append(text)

        if text_parts:
            return "\n".join(text_parts)

    return str(answer)

def target(inputs: dict) -> dict:

    question = inputs["question"].strip()

    if not question:
        raise ValueError(
            "Evaluation example contains an empty question."
        )

    documents = get_user_chunks(
        user_id=EVAL_USER_ID
    )

    if not documents:
        raise RuntimeError(
            f"No documents found for EVAL_USER_ID="
            f"'{EVAL_USER_ID}'"
        )

    result = ask_agent_with_trace(
        question=question,
        documents=documents,
        user_id=EVAL_USER_ID,
    )
    
    answer = extract_answer_text(
        result["answer"]
    )

    return {
    "answer": answer,
    "retrieved_documents": [
        {
            "page_content": document.page_content,
            "metadata": document.metadata,
            "rerank_score": float(score),
        }
        for document, score in result["retrieved_results"]
    ],
}