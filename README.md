# PDF Summarizer API

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)

A backend API that takes any PDF — research paper, report, contract, documentation — and returns a structured AI summary, key insights, and extracted topics in seconds. No manual reading. No copy-pasting into ChatGPT. Just upload and get results.

Built to explore how asynchronous task queues and LLMs can be combined into a reliable, scalable backend pipeline.

---

## Demo

> Upload a PDF → task queued → Celery worker processes it → Gemini AI summarizes → results ready to fetch

![Demo](./assets/demo.gif)

*Running locally via Docker Compose. Live hosting not available due to Gemini AI API costs on free infrastructure.*

---

## The Problem It Solves

Reading and extracting value from PDFs is something engineers, researchers, and businesses do constantly — and it's tedious at scale. This API automates that entire workflow:

- A user uploads a PDF
- The API immediately returns a task ID (non-blocking)
- In the background, text is extracted and sent to Gemini AI
- The structured result — summary, insights, topics — is stored and retrievable at any time

This pattern (async task queue + LLM processing) is directly applicable to real-world document automation pipelines.

---

## Features

- Upload PDF files via a single REST endpoint
- Non-blocking processing — API responds instantly, work happens in the background
- Automatic text extraction with PyPDF2
- Gemini AI generates a summary, key insights, and important topics per document
- Task state tracked from `PENDING` → `COMPLETED` (or `FAILED`)
- All results persisted in PostgreSQL — fetch anytime after processing
- Fully containerized — runs with a single `docker-compose up` command

---

## Sample API Response

After uploading a PDF and polling `GET /documents/{id}`:

```json
{
  "id": 7,
  "original_filename": "Mohammed Faraiz-Resume.pdf",
  "status": "completed",
  "summary": "Mohammed Faraiz is a detail-oriented professional with over 4 years of experience in risk management, data analysis, and client account handling. He has a proven track record in analytical investigations, process optimization, and technical problem-solving, coupled with strong communication and mentoring skills. His experience includes roles as a Screening Specialist at Randstad, a Concession Abuse Prevention Specialist at Amazon, and an Associate Account Manager at Sutherland.",
  "created_at": "2026-06-02T20:01:54.771903Z"
}
```

---

## Tech Stack

| Technology     | Purpose                     |
| -------------- | --------------------------- |
| Python         | Core language               |
| FastAPI        | API framework               |
| Celery         | Async background processing |
| Redis          | Task queue broker           |
| PostgreSQL     | Persistent storage          |
| SQLAlchemy     | ORM                         |
| Docker Compose | Multi-service orchestration |
| Gemini AI      | LLM summarization           |
| PyPDF2         | PDF text extraction         |

---

## Architecture

```text
Client uploads PDF
        ↓
FastAPI receives file
        ↓
PostgreSQL stores metadata  (status: PENDING)
        ↓
Task ID returned to client immediately
        ↓
Task pushed to Redis queue
        ↓
Celery Worker picks up task
        ↓
PyPDF2 extracts raw text
        ↓
Gemini AI generates summary + insights + topics
        ↓
Results saved to PostgreSQL  (status: COMPLETED)
        ↓
Client fetches result via GET /documents/{id}
```

---

## API Endpoints

| Method | Endpoint          | Description                           |
| ------ | ----------------- | ------------------------------------- |
| GET    | `/`               | Health check                          |
| POST   | `/upload`         | Upload PDF and queue for processing   |
| GET    | `/documents`      | List all processed documents          |
| GET    | `/documents/{id}` | Fetch summary for a specific document |

---

## Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/faraiz88/PDF-Summarizer-API.git
cd PDF-Summarizer-API
```

### 2. Create `.env`

```env
GOOGLE_API_KEY=your_gemini_api_key    # Get from Google AI Studio (free tier available)
DATABASE_URL=postgresql://username:password@postgres:5432/pdf_summarizer
REDIS_URL=redis://redis:6379/0
```

### 3. Start All Services

```bash
docker-compose up --build
```

This starts four services: FastAPI, PostgreSQL, Redis, and the Celery worker.

### 4. Open Swagger UI

```
http://127.0.0.1:8000/docs
```

---

## Known Limitations

- Scanned/image-based PDFs are not supported — PyPDF2 only extracts selectable text
- No authentication on endpoints yet
- Very large PDFs (100+ pages) may hit Gemini's input token limits
- Live deployment not hosted — Gemini AI API costs make free-tier hosting impractical

---

## License

MIT License

---

## Author

Mohammed Faraiz
