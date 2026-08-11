import os
import tempfile

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def load_pdf(
    contents: bytes,
    document_id: str,
    user_id: str,
    filename: str
) -> list[Document]:

    temp_path = os.path.join(
        tempfile.gettempdir(),
        f"{document_id}.pdf"
    )

    try:

        with open(temp_path, "wb") as f:
            f.write(contents)

        loader = PyPDFLoader(temp_path)

        documents = loader.load()

        for document in documents:
            document.metadata.update({
                "document_id": document_id,
                "user_id": user_id,
                "filename": filename,
                "file_type": "pdf"
            })

        return documents

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)