# PDF Summarizer API

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
[![Live API](https://img.shields.io/badge/Live%20API-Railway-blueviolet)](https://pdf-summarizer-api-production.up.railway.app/docs)

A backend API that accepts text-based PDFs and returns AI-generated summaries processed asynchronously using Celery and Gemini AI.

---

## Live Deployment

- **API:** https://pdf-summarizer-api-production.up.railway.app
- **Swagger Docs:** https://pdf-summarizer-api-production.up.railway.app/docs

---

## Demo

![Demo](./assets/Demo_gif.gif)

---

## What This Does

- Client uploads a PDF and gets a `document_id` back instantly
- A background worker extracts the text and sends it to Gemini AI
- The structured result is persisted in PostgreSQL and retrievable at any time

---

## Architecture

```
Client
  │
  ▼
┌─────────────────────────────────┐
│         FastAPI (Port 8000)     │  ← Validates file, extracts text in-memory,
│     Uvicorn ASGI Web Server     │    saves metadata to DB, returns 202 immediately
└────────────┬────────────────────┘
             │ process_pdf.delay(extracted_text, doc_id)
             ▼
┌─────────────────────────────────┐
│       Redis (Task Broker)       │  ← Transports extracted text to the worker
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│       Celery Worker             │  ← Calls Gemini 2.5 Flash, parses structured
│  (Background Processing)        │    output, writes result back to PostgreSQL
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│       PostgreSQL Database       │  ← Stores document metadata and AI summary
└─────────────────────────────────┘
```

**Why extract text in the API layer, not the worker?**
Railway runs the API and worker as separate containers with no shared filesystem. Passing a file path to the worker would fail — the file doesn't exist on the worker's container. The API extracts text into memory and passes the raw string through Redis, keeping the design stateless and container-safe.

**Why async at all?**
PDF extraction and LLM inference can each take several seconds. A synchronous design would block the API thread entirely. Celery + Redis decouples ingestion from processing, keeping the API responsive and workers independently scalable.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Web Framework | FastAPI | Async REST API, automatic OpenAPI docs |
| Task Queue | Celery | Background job processing |
| Message Broker | Redis 7 | Queue transport between API and workers |
| Database | PostgreSQL 16 + SQLAlchemy | Persistent document and summary storage |
| AI Model | Google Gemini 2.5 Flash | Structured PDF summarization |
| PDF Parsing | PyPDF2 | In-memory text extraction from uploads |
| Containerisation | Docker + Docker Compose | Multi-service environment |
| Deployment | Railway | Cloud hosting |

---

## API Endpoints

| Method | Endpoint | Status | Description |
|---|---|---|---|
| `GET` | `/` | 200 | Health check |
| `POST` | `/upload` | 202 | Upload a PDF and queue for processing |
| `GET` | `/documents` | 200 | List all processed documents |
| `GET` | `/documents/{id}` | 200 / 404 | Fetch a document with its AI summary |

### Upload Flow

```
POST /upload
  → validates file (PDF only, max 5MB, must contain extractable text)
  → extracts text in-memory via PyPDF2
  → rejects scanned/image-based PDFs with 422
  → saves Document record to PostgreSQL (status: "processing")
  → dispatches Celery task with extracted text via Redis
  → returns 202 immediately

(background) Celery worker
  → calls Gemini 2.5 Flash with extracted text
  → writes structured result back to PostgreSQL
  → sets status: "completed" (or "failed" on error)
```

### Example Request

```bash
curl -X POST https://pdf-summarizer-api-production.up.railway.app/upload \
  -F "file=@your_document.pdf"
```

### Example Upload Response (202)

```json

{
  "message": "PDF uploaded and queued for processing",
  "document_id": 8,
  "status": "processing"
}

```

### Example Document Response (200)

```json

{
  "id": 8,
  "original_filename": "Hyderabad_Weather_Report.pdf",
  "status": "completed",
  "summary": "On Wednesday, June 3, 2026, Hyderabad, Telangana, is experiencing warm, humid, and partly sunny conditions at 84.9°F (29.4°C). There is a high (65%) probability of intermittent rain and possible thunderstorms later today, especially in the late afternoon and evening, marking the early transition to the Southwest Monsoon.\n\nThe 5-day forecast predicts continued warm temperatures (around 93-95°F / 34-35°C) with daily rain chances of 55-60%. The current weather is consistent with the imminent arrival of the monsoon, typically between June 5-15. Residents are advised to stay hydrated, carry rain gear, drive cautiously, and take general health and safety precautions for the approaching monsoon season.",
  "created_at": "2026-06-03T02:30:36.488209"
}

```

---

## Local Setup

### Prerequisites

- Docker & Docker Compose
- A Gemini API key — [get one free at Google AI Studio](https://aistudio.google.com/)

### 1. Clone

```bash
git clone https://github.com/faraiz88/PDF-Summarizer-API.git
cd PDF-Summarizer-API
```

### 2. Environment Variables

```env
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://faraiz:yourpassword@postgres:5432/pdf_summarizer
REDIS_URL=redis://redis:6379/0
POSTGRES_PASSWORD=yourpassword
```

### 3. Start All Services

```bash
docker-compose up --build
```

Starts four containers: `api`, `worker`, `redis`, and `postgres`.

### 4. Open Swagger UI

```
http://localhost:8001/docs
```

---

## Project Structure

```
PDF-Summarizer-API/
├── app/
│   ├── main.py           # FastAPI routes, file validation, upload handling
│   ├── celery_worker.py  # Celery config, process_pdf task, Gemini integration
│   ├── models.py         # SQLAlchemy ORM — Document table
│   ├── schemas.py        # Pydantic response schemas
│   └── database.py       # DB engine, session factory, Base
├── docker-compose.yml    # Multi-service orchestration
├── Dockerfile            # Python image, dependency installation
├── requirements.txt      # Pinned dependencies
├── create_tables.py      # Database initialisation helper
└── .env.example          # Environment variable template
```

---

## License

MIT License

---

## Author

Mohammed Faraiz
