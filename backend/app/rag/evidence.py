from dataclasses import dataclass

from langchain_core.documents import Document


# ============================================================
# Configuration
# ============================================================

DEFAULT_EVIDENCE_THRESHOLD = 0.30


# ============================================================
# Evidence Result
# ============================================================

@dataclass(frozen=True)
class EvidenceResult:
    """
    Result returned by the evidence gate.

    `ranked_results` contains the actual evidence accepted
    by the gate together with the CrossEncoder scores.
    """

    sufficient: bool

    ranked_results: list[tuple[Document, float]]

    best_score: float | None


# ============================================================
# Evidence Gate
# ============================================================

def check_retrieval_evidence(
    ranked_results: list[tuple[Document, float]],
    threshold: float = DEFAULT_EVIDENCE_THRESHOLD,
) -> EvidenceResult:
    """
    Decide whether retrieved evidence is sufficiently relevant.

    Parameters
    ----------
    ranked_results:
        Documents already ranked by the CrossEncoder.

        Example:

            [
                (document_1, 4.82),
                (document_2, 3.91),
                (document_3, 1.42),
            ]

    threshold:
        Minimum CrossEncoder score required for accepting
        the retrieved evidence.

    Returns
    -------
    EvidenceResult

    Notes
    -----
    This gate is intentionally deterministic.

    It does NOT use an LLM judge.

    Offline LLM-as-a-judge evaluation is handled separately
    by the LangSmith evaluation pipeline.
    """

    # --------------------------------------------------------
    # No retrieved evidence
    # --------------------------------------------------------

    if not ranked_results:
        return EvidenceResult(
            sufficient=False,
            ranked_results=[],
            best_score=None,
        )

    # --------------------------------------------------------
    # Validate results
    # --------------------------------------------------------

    for document, score in ranked_results:

        if not isinstance(document, Document):
            raise TypeError(
                "Each retrieval result must contain "
                "a LangChain Document."
            )

        if not isinstance(score, (int, float)):
            raise TypeError(
                "Each retrieval score must be numeric."
            )

    # --------------------------------------------------------
    # Best relevance score
    # --------------------------------------------------------

    best_score = max(
        float(score)
        for _, score in ranked_results
    )

    # --------------------------------------------------------
    # Evidence decision
    # --------------------------------------------------------

    if best_score < threshold:

        return EvidenceResult(
            sufficient=False,
            ranked_results=[],
            best_score=best_score,
        )

    # --------------------------------------------------------
    # Evidence accepted
    # --------------------------------------------------------

    return EvidenceResult(
        sufficient=True,
        ranked_results=ranked_results,
        best_score=best_score,
    )