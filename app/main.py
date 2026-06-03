from fastapi import FastAPI, UploadFile, File, HTTPException
from app.celery_worker import process_pdf
from app.database import SessionLocal, Base, engine
from app.models import Document
from app.schemas import DocumentResponse
from app import models
import os
import shutil
import uuid
import logging



app = FastAPI()
Base.metadata.create_all(bind=engine)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "PDF Summarizer API is running"
    }
        

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
    logger.info(f"Upload request received: {file.filename}")

    # Validate filename
    if not file.filename:
        logger.warning("Upload attempted with missing filename")
        raise HTTPException(status_code=400, detail="File must have a name")

    # Validate extension
    if not file.filename.lower().endswith(".pdf"):
        logger.warning(f"Invalid file extension uploaded: {file.filename}")
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Validate content type
    if file.content_type != "application/pdf":
        logger.warning(f"Invalid content type uploaded: {file.content_type}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Read file
    contents = await file.read()

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    if len(contents) > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file.filename}")
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")

    # Extract text directly (NO FILE STORAGE)
    try:
        from PyPDF2 import PdfReader
        import io

        pdf_reader = PdfReader(io.BytesIO(contents))

        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() or ""

    except Exception as e:
        logger.error(f"Failed to extract text: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to extract PDF text")

    db = SessionLocal()

    try:
        # Create database record
        new_document = Document(
            original_filename=file.filename,
            stored_filename=None,  # no file stored anymore
            extracted_text=None,
            summary=None,
            status="processing"
        )

        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        logger.info(f"Database record created: {new_document.id}")

        # Send TEXT to Celery (NOT file path anymore)
        try:
            process_pdf.delay(extracted_text, new_document.id)

            logger.info(
                f"Celery task started for document ID: {new_document.id}"
            )

        except Exception as e:
            logger.error(f"Failed to start Celery task: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to start background task"
            )

        return {
            "message": "PDF uploaded successfully",
            "document_id": new_document.id,
            "original_filename": file.filename,
            "status": "processing started"
        }

    finally:
        db.close()