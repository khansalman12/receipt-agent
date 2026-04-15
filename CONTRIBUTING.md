# Contributing

Thanks for your interest in ReceiptAgent. Here's how to get set up.

## Local setup

```bash
git clone https://github.com/khansalman12/receipt-agent.git
cd receipt-agent
cp .env.example .env
# Add your GROQ_API_KEY to .env

docker-compose up
```

The API starts at `http://localhost:8000/api/`.

## Running tests

Tests use pytest with Django's test database. No external APIs are called -- all LLM interactions are mocked.

```bash
# Full suite
pytest api/tests/ -v

# With coverage
pytest api/tests/ --cov=api --cov-report=term-missing

# Single file
pytest api/tests/test_pipeline.py -v
```

## Linting

We use [ruff](https://docs.astral.sh/ruff/) for linting. CI will block PRs that fail the lint check.

```bash
pip install ruff
ruff check api/ config/
```

## Adding a new test

1. Pick the right test file (or create one under `api/tests/`)
2. Use the shared fixtures from `conftest.py` -- `expense_report`, `receipt`, `sample_image`
3. Mark database tests with `@pytest.mark.django_db`
4. Mock external calls -- never let tests hit real LLMs

## Pull requests

- One feature per PR
- Include tests for new behavior
- Keep the PR description short -- what changed and why
- CI must pass before merge

## Project layout

```
api/
  models.py         -- Django models
  views.py          -- DRF viewsets
  serializers.py    -- request/response validation
  tasks.py          -- Celery background tasks
  ai/
    graph.py        -- LangGraph workflow definition
    nodes.py        -- individual pipeline nodes
    state.py        -- typed state for the graph
  tests/            -- pytest test suite
  management/
    commands/        -- Django CLI commands
```
