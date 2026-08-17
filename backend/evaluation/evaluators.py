# This is the LangSmith-facing evaluator. This will call our judge.
from typing import Any

from evaluation.judge import judge_rag_response
from evaluation.config import (
    RUN_RETRIEVAL_RELEVANCE,
    RUN_GROUNDEDNESS,
    RUN_ANSWER_RELEVANCE,
    RUN_CORRECTNESS,
)


def _get_answer(outputs: dict[str, Any]) -> str:
    """
    Extract the generated answer from target.py output.
    """

    answer = outputs.get("answer", "")

    if not isinstance(answer, str):
        answer = str(answer)

    return answer.strip()


def _get_retrieved_documents(
    outputs: dict[str, Any],
) -> list[dict]:
    """
    Extract retrieved evidence from target.py output.
    """

    documents = outputs.get(
        "retrieved_documents",
        [],
    )

    if not isinstance(documents, list):
        return []

    return documents


def _get_question(
    inputs: dict[str, Any],
) -> str:
    """
    Extract the original evaluation question.
    """

    question = inputs.get(
        "question",
        "",
    )

    if not isinstance(question, str):
        question = str(question)

    return question.strip()


def _get_reference_answer(
    reference_outputs: dict[str, Any] | None,
) -> str | None:
    """
    Extract the reference answer from the LangSmith dataset.

    Reference output is needed only for correctness.
    """

    if not reference_outputs:
        return None

    answer = reference_outputs.get(
        "answer",
        "",
    )

    if not answer:
        return None

    if not isinstance(answer, str):
        answer = str(answer)

    return answer.strip()


def evaluate_rag(
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    reference_outputs: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Run all RAG evaluation metrics using ONE LLM judge call.

    LangSmith expects a list of score dictionaries:

        [
            {
                "key": "...",
                "score": 0.0 - 1.0,
            }
        ]

    The judge itself evaluates:
        - retrieval relevance
        - groundedness
        - answer relevance
        - correctness
    """

    question = _get_question(inputs)

    answer = _get_answer(outputs)

    retrieved_documents = _get_retrieved_documents(
        outputs
    )

    reference_answer = _get_reference_answer(
        reference_outputs
    )

    # --------------------------------------------------------
    # One LLM call
    # --------------------------------------------------------

    result = judge_rag_response(
        question=question,
        answer=answer,
        retrieved_documents=retrieved_documents,
        reference_answer=reference_answer,
    )

    # --------------------------------------------------------
    # Convert structured judge output into LangSmith scores
    # --------------------------------------------------------

    scores = []

    if (
        RUN_RETRIEVAL_RELEVANCE
        and result.retrieval_relevance is not None
    ):
        scores.append(
            {
                "key": "retrieval_relevance",
                "score": result.retrieval_relevance,
            }
        )


    if (
        RUN_GROUNDEDNESS
        and result.groundedness is not None
    ):
        scores.append(
            {
                "key": "groundedness",
                "score": result.groundedness,
            }
        )


    if (
        RUN_ANSWER_RELEVANCE
        and result.answer_relevance is not None
    ):
        scores.append(
            {
                "key": "answer_relevance",
                "score": result.answer_relevance,
            }
        )


    if (
        RUN_CORRECTNESS
        and result.correctness is not None
    ):
        scores.append(
            {
                "key": "correctness",
                "score": result.correctness,
            }
        )

    return scores