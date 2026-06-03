from celery import Celery
from dotenv import load_dotenv
from app.database import SessionLocal
from app.models import Document
import google.generativeai as genai
import os

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("models/gemini-2.5-flash")

REDIS_URL = os.getenv("REDIS_URL")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

def summarize_text(text: str):
    prompt = f"""
    You are an expert document summarizer.
    Create a concise summary:

    {text[:5000]}
    """
    response = model.generate_content(prompt)
    return response.text


@celery_app.task
def process_pdf(extracted_text, document_id):
    summary = summarize_text(extracted_text)

    db = SessionLocal()
    try:
        document = db.query(Document).filter(
            Document.id == document_id
        ).first()

        if document:
            document.extracted_text = extracted_text
            document.summary = summary
            document.status = "completed"

            db.commit()

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()

    return summary