# PDF Summarizer API

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
[![Live API](https://img.shields.io/badge/Live%20API-Railway-blueviolet)](https://pdf-summarizer-api-production.up.railway.app/docs)

A backend API that accepts any PDF and returns a structured AI-generated summary, key insights, and important topics — processed asynchronously via Celery and Gemini AI.

---

## Demo

![Demo](./assets/demo.gif)

---

## What Problem This Solves

Reading and extracting value from PDFs is something engineers, researchers, and businesses do constantly — and it's slow at scale. This API automates the entire workflow:

- Client uploads a PDF and gets a `document_id` back instantly
- A background worker extracts the text and sends it to Gemini AI
- The structured result is persisted in PostgreSQL and retrievable at any time

This pattern — async task queue + LLM processing — maps directly to real-world document automation pipelines used in legal, finance, and research tooling.

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
  → dispatches Celery task via Redis
  → returns 202 immediately

(background) Celery worker
  → receives extracted text from Redis
  → calls Gemini 2.5 Flash
  → writes result back to PostgreSQL
  → sets status: "completed" (or "failed" on error)
```

### Example Request

```bash
curl -X POST https://pdf-summarizer-api-production.up.railway.app/upload \
  -F "file=@your_document.pdf"
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
