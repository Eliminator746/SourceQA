from sqlalchemy.orm import Session

from app.models.document import Document
from app.rag.ingestion import ingest_documents
from app.rag.loaders import load_document
from app.services.s3_service import get_s3_object


def ingest_document_from_s3(
    document: Document,
    db: Session,
) -> None:
    """
    Ingest one document from its private S3 object.

    Flow:
        S3
        ↓
        bytes
        ↓
        loader
        ↓
        LangChain Documents
        ↓
        chunking + embeddings + Chroma
        ↓
        PostgreSQL status
    """

    try:

        # -----------------------------------------
        # Mark as processing
        # -----------------------------------------

        document.status = "processing"
        document.error_message = None

        db.commit()

        # -----------------------------------------
        # Download original document from S3
        # -----------------------------------------

        contents = get_s3_object(
            document.s3_key
        )

        if not contents:
            raise ValueError(
                "S3 object is empty"
            )

        # -----------------------------------------
        # Load PDF / DOCX / TXT
        # -----------------------------------------

        documents = load_document(
            contents=contents,
            file_type=document.file_type,
            document_id=str(document.id),
            user_id=str(document.user_id),
            filename=document.filename,
        )

        if not documents:
            raise ValueError(
                "No content could be extracted from document"
            )

        # -----------------------------------------
        # Chunk + embed + store in Chroma
        # -----------------------------------------

        chunks = ingest_documents(
            documents
        )

        if not chunks:
            raise ValueError(
                "Document produced no chunks"
            )

        # -----------------------------------------
        # Success
        # -----------------------------------------

        document.status = "ready"
        document.error_message = None

        db.commit()
        db.refresh(document)

    except Exception as exc:

        # -----------------------------------------
        # Failure
        # -----------------------------------------

        document.status = "failed"
        document.error_message = str(exc)

        db.commit()

        raise