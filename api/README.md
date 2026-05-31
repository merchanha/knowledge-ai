# Knowledge-AI API

FastAPI backend for Knowledge-AI — REST API at `/api/v1` and MCP server at `/mcp`.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker (for PostgreSQL and Redis)

## Setup

```bash
# Install dependencies
uv sync --all-extras --dev

# Copy environment template
cp .env.example .env

# Start infrastructure
docker compose up -d
```

## Run

```bash
uv run uvicorn knowledge_ai.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

## Development

```bash
uv run ruff check .
uv run ruff format .
uv run mypy .
uv run pytest
```
