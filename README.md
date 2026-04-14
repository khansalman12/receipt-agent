# ReceiptAgent

**AI-Powered Receipt Processing & Expense Management**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://djangoproject.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/khansalman12/receiptagent)

--- 

## What It Does

ReceiptAgent automatically processes expense receipts using AI agents:

- **OCR Extraction** - Upload receipt image, extract text via OpenCV
- **AI Parsing** - LLM extracts merchant, amount, date, line items into structured JSON
- **Fraud Detection** - Anomaly detection with risk scoring
- **Smart Validation** - Auto-validate against configurable expense policies
- **Async Processing** - Background processing with Celery + Redis

---

## Architecture

```
Client --> Django REST API --> PostgreSQL
                |
            Redis Queue
                |
          Celery Workers
                |
      LangGraph AI Pipeline
      [ OCR -> Extract -> Validate -> Fraud Check ]
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Groq API key ([free at console.groq.com](https://console.groq.com))

### Run Locally

```bash
git clone https://github.com/khansalman12/receiptagent.git
cd receiptagent

cp .env.example .env
# Add your GROQ_API_KEY to .env

docker-compose up -d
docker-compose exec web python manage.py migrate

# Test
curl http://localhost:8000/api/health/
```

---

## Deploy Free on Render.com

1. Fork/push this repo to your GitHub
2. Go to [render.com](https://render.com) -> New -> Blueprint
3. Connect the repo (Render reads `render.yaml` automatically)
4. Set `GROQ_API_KEY` in the Environment tab
5. Wait ~5 min, your app is live at `https://receiptagent.onrender.com`

> Free tier: app sleeps after 15 min inactivity, 750 hrs/month, 1GB Postgres, 25MB Redis

---

## API Endpoints

### Expense Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/` | List all reports |
| POST | `/api/reports/` | Create new report |
| GET | `/api/reports/{id}/` | Get single report |
| POST | `/api/reports/{id}/approve/` | Approve report |
| POST | `/api/reports/{id}/reject/` | Reject report |
| POST | `/api/reports/{id}/flag/` | Flag for review |

### Receipts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/receipts/` | List all receipts |
| POST | `/api/receipts/` | Upload receipt image |
| GET | `/api/receipts/{id}/` | Get receipt details |
| DELETE | `/api/receipts/{id}/` | Delete receipt |

---

## AI Pipeline

The LangGraph workflow processes receipts through these stages:

```
OCR Image -> Extract Fields -> Validate Check -> Fraud Score
   |              |                 |                |
Raw text     Structured JSON   Validated amounts  Risk score & flags
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.0, Django REST Framework |
| AI Framework | LangChain, LangGraph |
| LLM | Groq (Llama 3) - free tier |
| Task Queue | Celery + Redis |
| Database | PostgreSQL |
| Static Files | WhiteNoise |
| Deployment | Render.com (free) |
| Container | Docker, Docker Compose |

---

## Project Structure

```
receiptagent/
├── api/                    # Django API app
│   ├── models.py          # Data models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API endpoints
│   ├── tasks.py           # Celery async tasks
│   └── ai/                # AI pipeline
│       ├── state.py       # LangGraph state
│       ├── nodes.py       # Processing nodes
│       ├── graph.py       # Workflow graph
│       └── chains.py      # LLM chains
├── config/                # Django settings
├── docker-compose.yml     # Local dev services
├── Dockerfile             # Production container
├── render.yaml            # Render.com deploy config
├── build.sh               # Render build script
└── requirements.txt
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (False in prod) | No |
| `DATABASE_URL` | PostgreSQL connection | Yes |
| `REDIS_URL` | Redis connection | Yes |

---

## License

MIT License - Free to use and modify.

---

**Built with LangGraph + Django REST Framework**
