# ReceiptAgent

I built this to solve a genuinely annoying problem — manually logging receipts after business trips. You snap a photo, the AI reads it, pulls out the merchant, amount, date and line items, flags anything that looks suspicious, and stores it all in a structured expense report. No typing required.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://djangoproject.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

![ReceiptAgent Demo](docs/demo.gif)

---

## What it actually does

Upload a receipt image → the system runs it through an AI pipeline that:

1. **Reads the image** with OpenCV OCR — handles blurry, angled, crumpled receipts
2. **Extracts the data** using Llama 3 via Groq — merchant name, total amount, date, individual line items
3. **Validates it** — checks amounts add up, date is reasonable, required fields exist
4. **Scores fraud risk** — flags duplicate amounts, unusual vendors, outlier spending patterns
5. **Saves structured JSON** — ready to query, export, or review

All of this runs in the background via Celery so the API responds instantly and processing happens async.

---

## How to run it locally

You need Docker. That's it.

```bash
git clone https://github.com/khansalman12/receipt-agent.git
cd receipt-agent

# Copy env file and add your Groq API key (free at console.groq.com)
cp .env.example .env

# Start everything — migrations run automatically
docker-compose up
```

Give it 30 seconds on first run while Docker pulls the images. Then hit:

```bash
curl http://localhost:8000/api/health/
```

You should get a `200 OK`. You're good to go.

---

## Trying it out

```bash
# Create an expense report
curl -X POST http://localhost:8000/api/reports/ \
  -H "Content-Type: application/json" \
  -d '{"title": "April Business Trip", "description": "Client meetings in London"}'

# Upload a receipt image to that report
curl -X POST http://localhost:8000/api/receipts/ \
  -F "image=@receipt.jpg" \
  -F "report=1"

# Check the extracted data (wait a few seconds for processing)
curl http://localhost:8000/api/receipts/1/
```

The response comes back with merchant name, total, date, line items, fraud score, and validation status — all pulled from the image automatically.

---

## API reference

### Expense Reports

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/api/reports/` | List all reports |
| POST | `/api/reports/` | Create a new report |
| GET | `/api/reports/{id}/` | Get one report |
| POST | `/api/reports/{id}/approve/` | Approve it |
| POST | `/api/reports/{id}/reject/` | Reject it |
| POST | `/api/reports/{id}/flag/` | Flag for manual review |

### Receipts

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/api/receipts/` | List all receipts |
| POST | `/api/receipts/` | Upload a receipt image |
| GET | `/api/receipts/{id}/` | Get receipt + extracted data |
| DELETE | `/api/receipts/{id}/` | Delete it |

---

## How the AI pipeline works

I used LangGraph to build a stateful processing pipeline — each receipt moves through a series of nodes and only progresses if the previous step succeeds:

```
Upload Image
     ↓
  OCR Node          — OpenCV reads the raw text from the image
     ↓
 Extract Node       — Llama 3 parses the text into structured JSON
     ↓
 Validate Node      — checks totals, dates, required fields
     ↓
Fraud Check Node    — scores anomalies and flags suspicious patterns
     ↓
 Finalize Node      — saves everything to the database
```

If any step fails (bad image, unreadable text, validation error), the pipeline stops and returns a clear error instead of saving bad data.

---

## Tech stack

| Layer | What I used |
|-------|-------------|
| API | Django 5, Django REST Framework |
| AI pipeline | LangGraph, LangChain |
| LLM | Groq (Llama 3) — free tier |
| Background jobs | Celery + Redis |
| Database | PostgreSQL |
| Image processing | OpenCV |
| Container | Docker, Docker Compose |
| Static files | WhiteNoise |

---

## Project structure

```
receipt-agent/
├── api/
│   ├── models.py          — ExpenseReport and Receipt models
│   ├── views.py           — REST endpoints
│   ├── serializers.py     — request/response shapes
│   ├── tasks.py           — Celery async tasks
│   └── ai/
│       ├── graph.py       — LangGraph workflow definition
│       ├── nodes.py       — OCR, extract, validate, fraud nodes
│       ├── chains.py      — LLM prompt chains
│       └── state.py       — shared pipeline state
├── config/                — Django settings, Celery config
├── docker-compose.yml     — local dev stack
├── Dockerfile             — production container
└── requirements.txt
```

---

## Environment variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Get one free at [console.groq.com](https://console.groq.com) |
| `SECRET_KEY` | Any random string in production |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `DEBUG` | Set to `0` in production |

---

## License

MIT — do whatever you want with it.
