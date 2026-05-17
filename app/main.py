from fastapi import FastAPI, UploadFile, File, HTTPException
from app.celery_worker import process_pdf
from app.database import SessionLocal
from app.models import Document
from app.schemas import DocumentResponse
import os
import shutil
import uuid
import logging


app = FastAPI()

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get(
    "/documents/{document_id}",
    response_model=DocumentResponse
)
def get_document(document_id: int):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(
            Document.id == document_id
        ).first()
        if not document:
            logger.warning(
                f"Document not found: {document_id}"
            )
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )
        logger.info(
            f"Fetched document: {document_id}"
        )
        return document
    
    finally:
        db.close()


@app.get(
    "/documents",
    response_model=list[DocumentResponse]
)
def get_documents():
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        logger.info(
            f"Fetched {len(documents)} documents"
        )
        return documents

    finally:
        db.close()


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    logger.info(
        f"Upload request received: {file.filename}"
    )

    # Validate filename
    if not file.filename:

        logger.warning(
            "Upload attempted with missing filename"
        )
        raise HTTPException(
            status_code=400,
            detail="File must have a name"
        )

    # Validate extension
    if not file.filename.lower().endswith(".pdf"):

        logger.warning(
            f"Invalid file extension uploaded: {file.filename}"
        )
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF"
        )

    # Validate content type
    if file.content_type != "application/pdf":

        logger.warning(
            f"Invalid content type uploaded: {file.content_type}"
        )
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Validate file size
    contents = await file.read()
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    if len(contents) > MAX_FILE_SIZE:
        logger.warning(
            f"File too large: {file.filename}"
        )
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 5MB."
        )

    # Reset file pointer
    await file.seek(0)

    # Generate unique filename
    extension = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{extension}"

    # Full file path
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(
            f"PDF saved successfully: {unique_name}"
        )

    except Exception as e:

        logger.error(
            f"Failed to save file: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    db = SessionLocal()

    try:
        # Create database record
        new_document = Document(
            original_filename=file.filename,
            stored_filename=unique_name,
            status="processing"
        )

        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        logger.info(
            f"Database record created: {new_document.id}"
        )

        # Start Celery background task
        try:
            process_pdf.delay(
                file_path,
                new_document.id
            )

            logger.info(
                f"Celery task started for document ID: {new_document.id}"
            )

        except Exception as e:

            logger.error(
                f"Failed to start Celery task: {str(e)}"
            )

            raise HTTPException(
                status_code=500,
                detail=f"Failed to start background task: {str(e)}"
            )

        return {
            "message": "PDF uploaded successfully",
            "document_id": new_document.id,
            "stored_filename": unique_name,
            "original_filename": file.filename,
            "status": "processing started"
        }

    finally:
        db.close()



# from fastapi import FastAPI, UploadFile, File, HTTPException
# from celery_worker import process_pdf
# from database import SessionLocal
# from models import Document
# from schemas import DocumentResponse
# import os
# import shutil
# import uuid

# app = FastAPI()

# UPLOAD_DIR = "uploads"

# os.makedirs(UPLOAD_DIR, exist_ok=True)


# @app.get("/documents/{document_id}",
#          response_model=DocumentResponse)
# def get_document(document_id: int):
#     db = SessionLocal()
#     document = db.query(Document).filter(
#         Document.id == document_id
#     ).first()
#     db.close()
#     if not document:
#         raise HTTPException(
#             status_code=404,
#             detail="Document not found"
#         )
#     return document


# @app.get("/documents",
#          response_model=list[DocumentResponse])
# def get_documents():
#     db = SessionLocal()
#     documents = db.query(Document).all()
#     db.close()
#     return documents


# @app.post("/upload")
# async def upload_pdf(file: UploadFile = File(...)):

#     # Validate PDF
#     if file.content_type != "application/pdf":
#         raise HTTPException(
#             status_code=400,
#             detail="Only PDF files are allowed"
#         )

#     # Generate unique filename
#     extension = os.path.splitext(file.filename)[1]
#     unique_name = f"{uuid.uuid4()}{extension}"

#     # Full file path
#     file_path = os.path.join(UPLOAD_DIR, unique_name)

#     # Save file
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     db = SessionLocal()

#     try:
#         new_document = Document(
#             original_filename=file.filename,
#             stored_filename=unique_name,
#             status="processing"
#         )

#         db.add(new_document)
#         db.commit()
#         db.refresh(new_document)

#         # Pass Document ID To Celery
#         process_pdf.delay(file_path, new_document.id)

#     finally:
#         db.close()

#     return {
#         "message": "PDF uploaded successfully",
#         "stored_filename": unique_name,
#         "original_filename": file.filename,
#         "status": "processing started"
#     }


