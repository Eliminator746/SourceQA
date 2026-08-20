import uuid

import magic

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.services.s3_service import delete_s3_object, s3_upload
from app.services.rag_ingestion import (
    ingest_document_from_s3,
)


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


MAX_DOCUMENTS = 5
MAX_FILE_SIZE = 10 * 1024 * 1024


SUPPORTED_FILE_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}


def ingest_uploaded_document(document_id: uuid.UUID) -> None:
    db = SessionLocal()

    try:
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        if document:
            ingest_document_from_s3(document=document, db=db)
    except Exception:
        pass
    finally:
        db.close()


# =========================
# Upload document
# =========================

@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # -------------------------
    # Check document count
    # -------------------------

    document_count = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .count()
    )

    if document_count >= MAX_DOCUMENTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Maximum of 5 documents allowed. "
                "Delete an existing document before uploading another."
            )
        )

    # -------------------------
    # Read file
    # -------------------------

    contents = await file.read()

    file_size = len(contents)

    # -------------------------
    # Validate file size
    # -------------------------

    if not 0 < file_size <= MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be between 1 byte and 10 MB"
        )

    # -------------------------
    # Detect MIME type
    # -------------------------

    file_type = magic.from_buffer(
        contents,
        mime=True
    )

    if file_type not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_type}"
        )

    # -------------------------
    # Generate document ID
    # -------------------------

    document_id = uuid.uuid4()

    extension = SUPPORTED_FILE_TYPES[file_type]

    # -------------------------
    # S3 key
    # -------------------------

    document_key = (
        f"documents/"
        f"{current_user.id}/"
        f"{document_id}.{extension}"
    )

    # -----------------------------------------
    # Upload original file to S3
    # -----------------------------------------

    try:

        s3_upload(
            contents,
            document_key,
            file_type
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


    # -----------------------------------------
    # Save DB metadata
    # -----------------------------------------

    new_document = Document(
        id=document_id,
        user_id=current_user.id,
        filename=file.filename,
        file_type=extension,
        file_size=file_size,
        s3_key=document_key,
        status="processing",
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)


    # -----------------------------------------
    # S3 → RAG ingestion
    # -----------------------------------------

    background_tasks.add_task(
        ingest_uploaded_document,
        new_document.id,
    )

    return {
        "message": "Document uploaded and is being indexed",
        "document_id": new_document.id,
        "filename": new_document.filename,
        "status": new_document.status,
    }

# =========================
# Get all documents
# =========================

@router.get(
    "",
    response_model=DocumentListResponse
)
def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )

    return {
        "documents": documents,
        "count": len(documents),
        "max_sources": MAX_DOCUMENTS
    }


# =========================
# Get document
# =========================

@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return document


# =========================
# Delete document
# =========================

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK
)
def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete file from S3
    try:

        delete_s3_object(document.s3_key)

    except Exception:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document from storage"
        )

    # Delete metadata from PostgreSQL
    db.delete(document)
    db.commit()

    return {"message": "Document {document_id} - Deleted successfully"}