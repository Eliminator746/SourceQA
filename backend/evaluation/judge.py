# This contains one LLM judge.
from typing import Optional

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from evaluation.config import (
    JUDGE_MODEL,
    RUN_RETRIEVAL_RELEVANCE,
    RUN_GROUNDEDNESS,
    RUN_ANSWER_RELEVANCE,
    RUN_CORRECTNESS,
)


# ============================================================
# Structured Judge Output
# ============================================================

class JudgeResult(BaseModel):
    """
    Scores produced by the LLM judge.

    Every score is normalized to [0, 1].

    1.0 = excellent
    0.0 = completely fails the criterion
    """

    retrieval_relevance: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "How relevant the retrieved evidence is to the "
            "user's question."
        ),
    )

    groundedness: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "How well the claims in the generated answer are "
            "supported by the retrieved evidence."
        ),
    )

    answer_relevance: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "How directly and completely the generated answer "
            "addresses the user's question."
        ),
    )

    correctness: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "How factually correct the generated answer is "
            "compared with the reference answer."
        ),
    )


# ============================================================
# Judge Model
# ============================================================

judge_model = ChatGoogleGenerativeAI(
    model=JUDGE_MODEL
)


# ============================================================
# Structured Judge
# ============================================================

structured_judge = judge_model.with_structured_output(
    schema=JudgeResult.model_json_schema(),
    method="json_schema",
)


# ============================================================
# Helpers
# ============================================================

def _format_documents(
    retrieved_documents: list[dict],
    max_chars_per_document: int = 1500,
) -> str:
    """
    Convert retrieved documents into compact evaluation context.

    We deliberately cap each document's content to control
    evaluation token usage.
    """

    if not retrieved_documents:
        return "NO_RETRIEVED_EVIDENCE"

    formatted = []

    for index, document in enumerate(
        retrieved_documents,
        start=1,
    ):
        content = document.get(
            "page_content",
            "",
        )

        metadata = document.get(
            "metadata",
            {},
        )

        filename = metadata.get(
            "filename",
            "Unknown source",
        )

        page = metadata.get("page")

        if page is not None:
            source = f"{filename}, page {page + 1}"
        else:
            source = filename

        score = document.get(
            "rerank_score"
        )

        score_text = ""

        if score is not None:
            score_text = f"\nReranker score: {score}"

        formatted.append(
            f"""
Evidence {index}
Source: {source}{score_text}
Content:
{content[:max_chars_per_document]}
""".strip()
        )

    return "\n\n".join(formatted)


def _build_evaluation_instructions() -> str:
    """
    Build only the evaluation criteria enabled in config.py.

    This allows us to turn individual metrics on/off during
    development without changing the judge implementation.
    """

    instructions = []

    if RUN_RETRIEVAL_RELEVANCE:
        instructions.append(
            """
RETRIEVAL RELEVANCE

Evaluate whether the retrieved evidence is relevant to the
question.

Consider:
- Does the evidence contain information useful for answering
  the question?
- Are the important pieces of evidence present?
- Is the evidence mostly irrelevant or useful?

Score:
1.0 = highly relevant evidence
0.5 = partially relevant evidence
0.0 = irrelevant evidence
""".strip()
        )

    if RUN_GROUNDEDNESS:
        instructions.append(
            """
GROUNDEDNESS

Evaluate whether the generated answer is supported by the
retrieved evidence.

Consider every factual claim made in the answer.

Do NOT reward an answer merely because it sounds correct.

Score:
1.0 = all meaningful claims are supported by the evidence
0.5 = some claims are supported but others are unsupported
0.0 = the answer is unsupported or contradicts the evidence

If the answer correctly says that the documents do not contain
enough information, do not penalize it merely because the
evidence does not contain the requested fact.
""".strip()
        )

    if RUN_ANSWER_RELEVANCE:
        instructions.append(
            """
ANSWER RELEVANCE

Evaluate whether the generated answer directly answers the
user's question.

Consider:
- Does it address what was actually asked?
- Does it avoid unnecessary information?
- Does it provide enough information to satisfy the question?

Score:
1.0 = directly and sufficiently answers the question
0.5 = partially answers the question
0.0 = does not answer the question
""".strip()
        )

    if RUN_CORRECTNESS:
        instructions.append(
            """
CORRECTNESS

Compare the generated answer against the reference answer.

Consider:
- factual accuracy
- important facts
- numbers
- entities
- relationships between facts
- whether the answer misses a critical part of the reference

Do not require identical wording.

Score:
1.0 = substantively correct
0.5 = partially correct
0.0 = incorrect

For an intentionally unanswerable question, a response saying
that the answer cannot be determined from the provided documents
should receive a high correctness score when the reference answer
also indicates that the information is unavailable.
""".strip()
        )

    return "\n\n".join(instructions)


# ============================================================
# Main Judge Function
# ============================================================

def judge_rag_response(
    question: str,
    answer: str,
    retrieved_documents: list[dict],
    reference_answer: str | None = None,
) -> JudgeResult:
    """
    Evaluate one RAG response using a single LLM call.

    Parameters
    ----------
    question:
        User's original question.

    answer:
        Answer generated by our RAG application.

    retrieved_documents:
        Evidence returned by our retrieval pipeline.

    reference_answer:
        Ground-truth answer from the LangSmith dataset.
        Required only for correctness evaluation.

    Returns
    -------
    JudgeResult
        Structured scores for all enabled metrics.
    """

    evidence = _format_documents(
        retrieved_documents
    )

    evaluation_instructions = (
        _build_evaluation_instructions()
    )

    reference_section = ""

    if RUN_CORRECTNESS:
        reference_section = f"""
REFERENCE ANSWER

{reference_answer or "NO_REFERENCE_ANSWER_PROVIDED"}
"""

    prompt = f"""
You are an expert evaluator for a Retrieval-Augmented Generation
(RAG) system.

Your task is to evaluate the RAG system's response using ONLY the
information supplied below.

You are NOT the answering model.
You are an evaluator.

Do not use outside knowledge.

============================================================
USER QUESTION
============================================================

{question}

============================================================
RETRIEVED EVIDENCE
============================================================

{evidence}

============================================================
GENERATED ANSWER
============================================================

{answer}

============================================================
REFERENCE ANSWER
============================================================

{reference_section}

============================================================
EVALUATION CRITERIA
============================================================

{evaluation_instructions}

============================================================
SCORING REQUIREMENTS
============================================================

Return a score between 0.0 and 1.0 for every enabled metric.

Use the full range when appropriate.

Do not infer missing evidence from your own knowledge.

The retrieved evidence is the only evidence available to the
RAG system.

If a metric is disabled, return null for that metric.

Return ONLY the requested structured output.
"""

    result = structured_judge.invoke(
        prompt
    )

    return JudgeResult.model_validate(
        result
    )