# PDF Summarizer API

> **Production-deployed** AI backend that accepts PDF uploads, extracts text, and returns structured AI summaries with key insights and important topics — built for scale with a fully asynchronous processing pipeline.

[![Live API](https://img.shields.io/badge/Live%20API-Railway-blueviolet?style=for-the-badge)](https://pdf-summarizer-api-production.up.railway.app/docs)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.x-37814A?style=for-the-badge)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)](https://docs.docker.com/compose/)
[![Gemini AI](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?style=for-the-badge&logo=google)](https://deepmind.google/technologies/gemini/)

---

## What This Project Does

Most teams waste hours manually reading through long reports, research papers, and contracts. This API solves that — upload any PDF and within seconds the system returns a structured AI-generated response containing a concise summary, key insights, and important topics covered, powered by Google Gemini 2.5 Flash.

The core design principle is **non-blocking processing**: the API accepts the file and returns immediately with a `document_id`, while a background Celery worker handles the heavy AI processing. The client polls for results when ready.

---

## Live Demo

| Resource | Link |
|---|---|
| Swagger UI (Interactive Docs) | https://pdf-summarizer-api-production.up.railway.app/docs |
| Base API | https://pdf-summarizer-api-production.up.railway.app |

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
│       PostgreSQL Database       │  ← Stores document metadata, extracted text,
│      (Persistent Storage)       │    AI summary, and processing status
└─────────────────────────────────┘
```

**Why extract text in the API layer, not the worker?**
Railway runs the API and worker as separate containers with no shared filesystem. Passing a file path to the worker would fail — the file doesn't exist on the worker's container. Instead, the API extracts text into memory and sends the raw string through Redis, making the design both correct and container-safe.

**Why async at all?**
PDF text extraction and LLM inference can each take several seconds. A synchronous design would block the API thread entirely. The Celery + Redis pattern decouples ingestion from processing, keeping the API responsive under load and making workers independently scalable.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Web Framework | FastAPI | Async REST API, automatic OpenAPI docs |
| Task Queue | Celery | Distributed background job processing |
| Message Broker | Redis 7 | Queue transport between API and workers |
| Database | PostgreSQL 16 + SQLAlchemy | Persistent document and summary storage |
| AI Model | Google Gemini 2.5 Flash | Structured PDF summarization |
| PDF Parsing | PyPDF2 | In-memory text extraction from uploads |
| Containerisation | Docker + Docker Compose | Reproducible multi-service environment |
| Deployment | Railway | Production cloud hosting |

---

## API Endpoints

| Method | Endpoint | Status Code | Description |
|---|---|---|---|
| `GET` | `/` | 200 | Health check — confirms API is running |
| `POST` | `/upload` | 202 | Upload a PDF; queues background processing |
| `GET` | `/documents` | 200 | List all processed documents |
| `GET` | `/documents/{id}` | 200 / 404 | Fetch a single document with its summary |

### Upload Flow

```
POST /upload
  → validates file (PDF only, max 5MB, must contain extractable text)
  → extracts text in-memory via PyPDF2
  → rejects scanned/image-based PDFs with 422
  → saves Document record to PostgreSQL (status: "processing")
  → dispatches Celery task with extracted text via Redis
  → returns 202 { "document_id": 42, "status": "processing" }

(background) Celery worker
  → receives extracted text from Redis
  → calls Gemini 2.5 Flash — returns summary, key insights, important topics
  → writes structured result back to PostgreSQL
  → sets status: "completed" (or "failed" on error)

GET /documents/42
  → returns document with full AI-generated summary
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
  "document_id": 7,
  "status": "processing"
}
```

### Example Document Response (200)

```json
{
  "id": 7,
  "original_filename": "research_paper.pdf",
  "status": "completed",
  "summary": "1. Summary: This paper investigates...\n2. Key Insights:\n- ...\n3. Important Topics: ...",
  "extracted_text": "Full extracted text...",
  "created_at": "2025-06-03T10:22:00Z"
}
```

---

## Validation & Error Handling

Multiple layers of validation protect every upload before any database or AI resources are touched:

| Check | Error |
|---|---|
| Missing filename | `400` File must have a name |
| Wrong extension | `400` File must be a PDF |
| Wrong content-type | `400` Only PDF files are allowed |
| File exceeds 5MB | `400` File size exceeds 5MB limit |
| Scanned / image-based PDF | `422` Could not extract text |
| Document not found | `404` Document not found |
| Gemini or DB failure | Sets `status: "failed"` in DB, re-raises exception |

---

## Local Setup

### Prerequisites

- Docker & Docker Compose
- A Google Gemini API key — [get one here](https://aistudio.google.com/)

### 1. Clone

```bash
git clone https://github.com/faraiz88/PDF-Summarizer-API.git
cd PDF-Summarizer-API
```

### 2. Environment Variables

Create a `.env` file (see `.env.example`):

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

This starts four containers simultaneously: `api`, `worker`, `redis`, and `postgres`.

### 4. Open the Docs

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
├── docker-compose.yml    # Multi-service orchestration (api, worker, redis, postgres)
├── Dockerfile            # Python image, dependency installation
├── requirements.txt      # Pinned dependencies
├── create_tables.py      # Database initialisation helper
└── .env.example          # Environment variable template
```

---

## Key Design Decisions

**Container-safe file handling**
Railway deploys each service as an isolated container. Storing the uploaded file to disk and passing a path to the worker would break — the worker has no access to the API container's filesystem. The API extracts text into memory and passes it through Redis, keeping the architecture stateless and cloud-native.

**`status: "failed"` on worker errors**
If Gemini's API is down, rate-limits, or throws any exception, the Celery task catches it, opens a fresh DB session, and marks the document as `"failed"` before re-raising. This prevents documents from being stuck in `"processing"` forever.

**Structured AI output**
The Gemini prompt explicitly requests three sections — a concise summary, bullet-point key insights, and a list of important topics. This makes the API output consistently parseable rather than free-form text.

**202 Accepted on upload**
The upload endpoint returns `202 Accepted` rather than `200 OK` to correctly signal that processing is asynchronous. `200` means "done"; `202` means "received and queued."

---

## What I'd Add Next

- [ ] `GET /tasks/{task_id}` — Celery task status polling endpoint
- [ ] Re-summarise endpoint — trigger a new Gemini pass with a custom prompt
- [ ] JWT authentication — per-user document isolation
- [ ] Large PDF chunking — split documents and summarise in parallel Celery tasks
- [ ] Upstash Redis + Neon PostgreSQL — managed cloud services, lower cold-start
- [ ] Prometheus + Grafana — task throughput and latency observability

---

## Author

**Mohammed Faraiz**

[![GitHub](https://img.shields.io/badge/GitHub-faraiz88-181717?style=flat&logo=github)](https://github.com/faraiz88)
