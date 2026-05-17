#  PDF Summarizer API

AI-powered backend system that automates PDF document processing and generates structured AI summaries, key insights, and important topics from uploaded files. Built with FastAPI, Celery, Redis, PostgreSQL, Docker, and Gemini AI for scalable asynchronous processing.
---

## ✨ Features

* Upload and process PDF documents
* Extract text from PDFs automatically
* AI-generated summaries using Gemini AI
* Asynchronous background processing with Celery
* Redis-powered task queue
* PostgreSQL database integration
* Dockerized multi-service architecture
* REST API with Swagger documentation
* Production-ready backend structure

---

## 🛠 Tech Stack

* Python
* FastAPI
* Celery
* Redis
* PostgreSQL
* SQLAlchemy
* Docker & Docker Compose
* Gemini AI API
* PyPDF2

---

## 🏗 Architecture

```text
Client Request
      ↓
FastAPI Upload Endpoint
      ↓
PostgreSQL stores metadata
      ↓
Celery queues background task
      ↓
Redis broker handles queue
      ↓
Celery Worker processes PDF
      ↓
Gemini AI generates summary
      ↓
Results stored and returned via API
```

---

## 🌐 API Endpoints

| Method | Endpoint          | Description                 |
| ------ | ----------------- | --------------------------- |
| POST   | `/upload`         | Upload PDF for processing   |
| GET    | `/documents`      | Get all processed documents |
| GET    | `/documents/{id}` | Get single document details |

---

## ⚙ Local Setup

### 📥 Clone Repository

```bash
git clone https://github.com/faraiz88/PDF-Summarizer-API.git
cd PDF-Summarizer-API
```

### 🔐 Create Environment Variables

Create `.env`

```env
GOOGLE_API_KEY=your_api_key
DATABASE_URL=postgresql://username:password@postgres:5432/pdf_summarizer
REDIS_URL=redis://redis:6379/0
```

### ▶ Start Application

```bash
docker-compose up --build
```

### 📄 Open API Docs

```text
http://127.0.0.1:8000/docs
```

---

## 🚀 Highlights

* Scalable asynchronous architecture using Celery + Redis
* Containerized multi-service backend with Docker Compose
* AI-powered document summarization workflow
* Clean modular backend structure with FastAPI
* Persistent PostgreSQL data storage
* Production-oriented API design and task processing

---

## 👨‍💻 Author

Mohammed Faraiz

