from collections import defaultdict

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)


def chunk_documents(
    documents: list[Document]
) -> list[Document]:

    chunks = text_splitter.split_documents(
        documents
    )

    counters = defaultdict(int)

    for chunk in chunks:

        document_id = chunk.metadata["document_id"]

        chunk.metadata["chunk_index"] = (
            counters[document_id]
        )

        counters[document_id] += 1

    return chunks