from dataclasses import dataclass

from langchain_core.documents import Document


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DEFAULT_EVIDENCE_THRESHOLD = 0.30


# ---------------------------------------------------------
# Evidence Result
# ---------------------------------------------------------

@dataclass
class EvidenceResult:
    """
    Result returned by the evidence gate.
    """

    sufficient: bool
    documents: list[Document]
    best_score: float | None


# ---------------------------------------------------------
# Evidence Gate
# ---------------------------------------------------------

def check_evidence(
    documents: list[Document],
    scores: list[float],
    threshold: float = DEFAULT_EVIDENCE_THRESHOLD,
) -> EvidenceResult:
    """
    Decide whether the retrieved documents contain
    sufficient evidence to answer the user's question.

    Parameters
    ----------
    documents:
        Documents returned by the reranker.

    scores:
        Cross-encoder relevance scores corresponding
        to the documents.

    threshold:
        Minimum relevance score required for accepting
        the retrieved evidence.

    Returns
    -------
    EvidenceResult
    """

    # ---------------------------------------------
    # No retrieved documents
    # ---------------------------------------------

    if not documents or not scores:
        return EvidenceResult(
            sufficient=False,
            documents=[],
            best_score=None,
        )

    # ---------------------------------------------
    # Safety check
    # ---------------------------------------------

    if len(documents) != len(scores):
        raise ValueError(
            "Number of documents must match "
            "number of scores."
        )

    # ---------------------------------------------
    # Best relevance score
    # ---------------------------------------------

    best_score = max(scores)

    # ---------------------------------------------
    # Evidence decision
    # ---------------------------------------------

    if best_score < threshold:
        return EvidenceResult(
            sufficient=False,
            documents=[],
            best_score=best_score,
        )

    return EvidenceResult(
        sufficient=True,
        documents=documents,
        best_score=best_score,
    )
    
    



def check_retrieval_evidence(
    ranked_results: list[tuple[Document, float]],
    threshold: float = DEFAULT_EVIDENCE_THRESHOLD,
) -> EvidenceResult:

    if not ranked_results:
        return EvidenceResult(
            sufficient=False,
            documents=[],
            best_score=None,
        )

    documents = [
        document
        for document, score in ranked_results
    ]

    scores = [
        float(score)
        for document, score in ranked_results
    ]

    return check_evidence(
        documents=documents,
        scores=scores,
        threshold=threshold,
    )