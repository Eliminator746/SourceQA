from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from app.rag.ingestion import vector_store


# ---------------------------------------------------------
# 1. Create Hybrid Retriever
# ---------------------------------------------------------

def create_retriever(
    documents: list[Document],
    user_id: str,
    semantic_k: int = 20,
    bm25_k: int = 20
):
    semantic_retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": semantic_k,
            "filter": {
                "user_id": user_id
            }
        }
    )

    bm25_retriever = BM25Retriever.from_documents(
        documents
    )   # returns a BM25Retriever object.

    bm25_retriever.k = bm25_k

    hybrid_retriever = EnsembleRetriever(
        retrievers=[
            semantic_retriever,
            bm25_retriever
        ],
        weights=[0.5, 0.5], # The weights=[0.5, 0.5] says you're giving the two retrievers equal weight.
        c=60
    )   # RRF technique

    return hybrid_retriever # will return you retrieved Document chunks at invoke


# ---------------------------------------------------------
# 2. Cross Encoder Reranker
# ---------------------------------------------------------

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def rerank_documents(
    question: str,
    documents: list[Document],
    top_k: int = 5
):
    """
    Rerank retrieved documents using a CrossEncoder.

    Returns:
        list[tuple[Document, float]]

    Each tuple contains:
        (document, relevance_score)
    """

    if not documents:
        return []

    pairs = [
        (
            question,
            document.page_content
        )
        for document in documents
    ]

    scores = reranker.predict(pairs)

    ranked_documents = sorted(
        zip(documents, scores),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        (
            document,
            float(score)
        )
        for document, score
        in ranked_documents[:top_k]
    ]


# ---------------------------------------------------------
# 3. Convenience Function
# ---------------------------------------------------------

def retrieve(
    question: str,
    documents: list[Document],
    user_id: str,
    semantic_k: int = 20,
    bm25_k: int = 20,
    rerank_k: int = 5
):
    """
    Complete retrieval pipeline:

    Chroma semantic search
            +
    BM25 keyword search
            ↓
       EnsembleRetriever
            ↓
            RRF
            ↓
       CrossEncoder
            ↓
       Top K documents
       + relevance scores
    """

    # ---------------------------------------------
    # Hybrid retrieval
    # ---------------------------------------------

    retriever = create_retriever(
        documents=documents,
        user_id=user_id,
        semantic_k=semantic_k,
        bm25_k=bm25_k
    )

    hybrid_documents = retriever.invoke(
        question
    )

    # ---------------------------------------------
    # Reranking
    # ---------------------------------------------

    ranked_results = rerank_documents(
        question=question,
        documents=hybrid_documents,
        top_k=rerank_k
    )

    return ranked_results