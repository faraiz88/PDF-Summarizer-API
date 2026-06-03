from fastapi import FastAPI, UploadFile, File, HTTPException
from PyPDF2 import PdfReader
from app.celery_worker import process_pdf
from app.database import SessionLocal, Base, engine
from app.models import Document
from app.schemas import DocumentResponse
from app import models
import io
import os
import logging

app = FastAPI()
Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "PDF Summarizer API is running"}


@app.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        logger.info(f"Fetched document: {document_id}")
        return document
    finally:
        db.close()


@app.get("/documents", response_model=list[DocumentResponse])
def get_documents():
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        logger.info(f"Fetched {len(documents)} documents")
        return documents
    finally:
        db.close()


@app.post("/upload", status_code=202)
async def upload_pdf(file: UploadFile = File(...)):
    logger.info(f"Upload request received: {file.filename}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a name")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    contents = await file.read()

    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

    pdf_reader = PdfReader(io.BytesIO(contents))
    extracted_text = ""
    for page in pdf_reader.pages:
        extracted_text += page.extract_text() or ""

    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text. File may be scanned or image-based."
        )

    db = SessionLocal()
    try:
        new_document = Document(
            original_filename=file.filename,
            extracted_text=None,
            summary=None,
            status="processing"
        )
        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        process_pdf.delay(extracted_text, new_document.id)

        logger.info(f"Document queued: {new_document.id}")

        return {
            "message": "PDF uploaded and queued for processing",
            "document_id": new_document.id,
            "status": "processing"
        }
    finally:
        db.close()