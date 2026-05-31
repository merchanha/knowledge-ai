# Knowledge-AI

Knowledge management system with REST API, MCP server for coding agents, and React admin panel.

## Monorepo Structure

| Folder | Description |
|--------|-------------|
| [`api/`](api/) | Python FastAPI backend (REST + MCP) |
| [`client/`](client/) | React SPA frontend (Week 15+) |

See the project brief (local only) for full architecture and stack details.

## Quick Start (API)

```bash
cd api
uv sync --all-extras --dev
cp .env.example .env
docker compose up -d
uv run uvicorn knowledge_ai.main:app --reload --port 8000
```

Health check: http://localhost:8000/api/v1/health
