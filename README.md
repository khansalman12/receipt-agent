# ReceiptAgent

**AI-Powered Receipt Processing & Expense Management**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://djangoproject.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

![ReceiptAgent Demo](docs/demo.gif)

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

## Quick Start (2 commands)

### Prerequisites
- Docker & Docker Compose
- Free Groq API key from [console.groq.com](https://console.groq.com)

```bash
git clone https://github.com/khansalman12/receipt-agent.git
cd receipt-agent

# Add your GROQ_API_KEY to .env
cp .env.example .env && open .env

# Start everything (auto-migrates, no extra steps)
docker-compose up
```

API is live at `http://localhost:8000`

### Test it

```bash
# Health check
curl http://localhost:8000/api/health/

# Create an expense report
curl -X POST http://localhost:8000/api/reports/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Business Trip", "description": "April expenses"}'

# Upload a receipt image
curl -X POST http://localhost:8000/api/receipts/ \
  -F "image=@/path/to/receipt.jpg" \
  -F "report=1"
```

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
