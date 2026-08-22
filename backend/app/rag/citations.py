from dataclasses import dataclass
from typing import Any


# ============================================================
# Citation
# ============================================================

@dataclass(frozen=True, slots=True)
class Citation:
    """
    Source attribution for evidence retrieved from a document.

    This object contains only metadata required by the frontend
    to identify the source of an answer.
    """

    document_id: str
    filename: str
    page: int | None = None
    chunk_index: int | None = None


# ============================================================
# Metadata helpers
# ============================================================

def _normalize_page(metadata: dict[str, Any]) -> int | None:
    """
    Normalize document page metadata to a 1-based integer.

    PyPDFLoader commonly stores `page` as a zero-based integer.

    Example:

        page = 0  ->  page = 1
        page = 1  ->  page = 2

    If a valid numeric page cannot be determined, return None.
    """

    raw_page = metadata.get("page")

    if raw_page is None:
        return None

    try:
        return int(raw_page) + 1
    except (TypeError, ValueError):
        return None


def _normalize_chunk_index(
    metadata: dict[str, Any],
) -> int | None:
    """
    Normalize chunk_index to an integer.
    """

    raw_chunk_index = metadata.get("chunk_index")

    if raw_chunk_index is None:
        return None

    try:
        return int(raw_chunk_index)
    except (TypeError, ValueError):
        return None


# ============================================================
# Citation builder
# ============================================================

def build_citations(
    ranked_results: list[tuple],
    max_citations: int = 3,
) -> list[Citation]:
    """
    Build deterministic citations from retrieved evidence.

    Parameters
    ----------
    ranked_results:
        Reranked/evidence-gated results in the form:

            [
                (Document, relevance_score),
                ...
            ]

    max_citations:
        Maximum number of unique citations returned.

    Returns
    -------
    list[Citation]

    Notes
    -----
    Citations are generated from document metadata rather than
    from the LLM response.

    Results are assumed to already be ordered by relevance.
    """

    if not ranked_results:
        return []

    if max_citations <= 0:
        return []

    citations: list[Citation] = []

    # Used to avoid returning the same source repeatedly.
    seen: set[tuple[str, int | None]] = set()

    for document, _score in ranked_results:

        metadata = document.metadata or {}

        # ----------------------------------------------------
        # Required metadata
        # ----------------------------------------------------

        document_id = metadata.get("document_id")
        filename = metadata.get("filename")

        # A chunk without these fields cannot be safely cited.
        if not document_id or not filename:
            continue

        document_id = str(document_id)
        filename = str(filename)

        # ----------------------------------------------------
        # Page
        # ----------------------------------------------------

        page = _normalize_page(metadata)

        # ----------------------------------------------------
        # Chunk
        # ----------------------------------------------------

        chunk_index = _normalize_chunk_index(metadata)

        # ----------------------------------------------------
        # Deduplication
        # ----------------------------------------------------
        #
        # If multiple chunks from the same page are retrieved:
        #
        #   chunk 3 -> page 2
        #   chunk 4 -> page 2
        #
        # return one citation:
        #
        #   document.pdf, page 2
        #
        # For documents without page metadata:
        #
        #   document_id + None
        #
        # becomes the deduplication key.
        # ----------------------------------------------------

        citation_key = (
            document_id,
            page,
        )

        if citation_key in seen:
            continue

        seen.add(citation_key)

        citations.append(
            Citation(
                document_id=document_id,
                filename=filename,
                page=page,
                chunk_index=chunk_index,
            )
        )

        if len(citations) >= max_citations:
            break

    return citations