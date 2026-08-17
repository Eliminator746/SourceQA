# app/rag/citations.py

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Citation:
    """
    Citation generated from retrieved Document metadata.

    This class intentionally contains only information
    that is useful to the frontend for source attribution.
    """

    document_id: str
    filename: str
    page: int | None = None
    chunk_index: int | None = None


def build_citations(
    ranked_results: list[tuple],
    max_citations: int = 3,
) -> list[Citation]:
    """
    Build deterministic citations from reranked Documents.

    Parameters
    ----------
    ranked_results:
        List of:
            (Document, relevance_score)

    max_citations:
        Maximum number of unique citations returned.

    Returns
    -------
    list[Citation]
    """

    if not ranked_results:
        return []

    citations: list[Citation] = []
    seen: set[tuple] = set()

    for document, _score in ranked_results:

        metadata = document.metadata or {}

        document_id = metadata.get("document_id")
        filename = metadata.get("filename")

        # A retrieved chunk without these fields cannot
        # be safely cited.
        if not document_id or not filename:
            continue

        # -------------------------------------------------
        # Page handling
        # -------------------------------------------------
        #
        # PyPDFLoader commonly stores page as 0-based.
        # Frontend users expect page numbers starting from 1.
        #
        # If page_label exists, prefer it.
        # Otherwise convert numeric page to 1-based.
        # -------------------------------------------------

        page = None

        if metadata.get("page_label") is not None:

            page = metadata["page_label"]

        elif metadata.get("page") is not None:

            raw_page = metadata["page"] # PyPDFLoader only automatically adds: metadata['pages']

            try:
                page = int(raw_page) + 1
            except (TypeError, ValueError):
                page = None

        # -------------------------------------------------
        # Chunk index
        # -------------------------------------------------

        chunk_index = metadata.get(
            "chunk_index"
        )

        if chunk_index is not None:

            try:
                chunk_index = int(chunk_index)

            except (TypeError, ValueError):
                chunk_index = None

        # -------------------------------------------------
        # Deduplicate citations
        # -------------------------------------------------
        #
        # Multiple chunks from the same document/page
        # should normally produce one citation.
        #
        # For TXT/DOCX without pages, document_id alone
        # becomes the deduplication key.
        # -------------------------------------------------

        if page is not None:

            citation_key = (
                str(document_id),
                page,
            )

        else:

            citation_key = (
                str(document_id),
                None,
            )

        if citation_key in seen:
            continue

        seen.add(citation_key)

        citations.append(
            Citation(
                document_id=str(document_id),
                filename=str(filename),
                page=page,
                chunk_index=chunk_index,
            )
        )

        if len(citations) >= max_citations:
            break

    return citations