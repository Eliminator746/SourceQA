import uuid

import magic

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.services.s3_service import s3_upload


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


# =========================
# Upload document
# =========================

@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document(
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

    # -------------------------
    # Upload to S3
    # -------------------------

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

    # -------------------------
    # Save DB record
    # -------------------------

    new_document = Document(
        id=document_id,
        user_id=current_user.id,
        filename=file.filename,
        file_type=extension,
        file_size=file_size,
        s3_key=document_key,
        status="processing"
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return {
        "message": "Document uploaded successfully",
        "document_id": new_document.id,
        "filename": new_document.filename,
        "status": new_document.status
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
    status_code=status.HTTP_204_NO_CONTENT
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

    # We will delete the S3 object here.
    # Chroma deletion will also be added later.

    db.delete(document)
    db.commit()

    return None