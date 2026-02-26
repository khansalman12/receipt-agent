# 🧾 ReceiptAgent

**AI-Powered Receipt Processing & Expense Management**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://djangoproject.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

--- 

## 🎯 What It Does

ReceiptAgent automatically processes expense receipts using AI:

- **📷 OCR Extraction** - Upload receipt image → Extract text
- **🤖 AI Parsing** - LLM extracts merchant, amount, date, items
- **🚨 Fraud Detection** - Anomaly detection and risk scoring
- **✅ Smart Validation** - Auto-validate against expense policies
- **⚡ Async Processing** - Background processing with Celery

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       RECEIPTAGENT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📱 Client → 🌐 Django REST API → 🗄️ PostgreSQL                │
│                      ↓                                          │
│                  🔴 Redis Queue                                 │
│                      ↓                                          │
│              📦 Celery Workers                                  │
│                      ↓                                          │
│          🤖 LangGraph AI Pipeline                              │
│          ┌─────────────────────────┐                           │
│          │ OCR → Extract → Validate │                           │
│          │     → Fraud Check        │                           │
│          └─────────────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Groq API key (free tier available)

### Run Locally

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/receiptagent.git
cd receiptagent

# Create environment file
cp .env.example .env
# Add your GROQ_API_KEY to .env

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Access the API
curl http://localhost:8000/api/health/
```

---

## 📋 API Endpoints

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

## 🧠 AI Pipeline

The LangGraph workflow processes receipts through these stages:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   OCR    │ →  │ Extract  │ →  │ Validate │ →  │  Fraud   │
│  Image   │    │  Fields  │    │  Check   │    │  Score   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     ↓               ↓               ↓               ↓
  Raw text      Structured       Validated       Risk score
  from image    JSON data        amounts         & flags
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Django 5.0, Django REST Framework |
| **AI Framework** | LangChain, LangGraph |
| **LLM Provider** | Groq (Llama 3) |
| **Task Queue** | Celery + Redis |
| **Database** | PostgreSQL |
| **Container** | Docker, Docker Compose |

---

## 📁 Project Structure

```
receiptagent/
├── api/                    # Django API app
│   ├── models.py          # Data models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API endpoints
│   └── ai/                # AI pipeline
│       ├── state.py       # LangGraph state
│       ├── nodes.py       # Processing nodes
│       ├── graph.py       # Workflow graph
│       └── chains.py      # LLM chains
├── config/                # Django settings
├── docker-compose.yml     # Services config
├── Dockerfile            # Container build
└── README.md
```

---

## 🔧 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (False in prod) | No |
| `DATABASE_URL` | PostgreSQL connection | Yes |
| `REDIS_URL` | Redis connection | Yes |

---

## 📊 Features

- ✅ REST API with full CRUD operations
- ✅ Async receipt processing with Celery
- ✅ AI-powered data extraction
- ✅ Fraud detection scoring
- ✅ Docker containerization
- ✅ PostgreSQL + Redis stack
- ⏳ Frontend dashboard (coming soon)

---

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

---

## 📝 License

MIT License - Free to use and modify.

---

**Built with LangGraph + Django REST Framework** 🚀
