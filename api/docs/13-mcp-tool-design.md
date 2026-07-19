# 13 — MCP Tool Design: Search & Command Browse

> **Audience:** Junior Python developers. Week 13 exposes existing domain services as MCP tools — same business logic as REST, different transport and response shape.

## What We Built

- **`search_knowledge_neurons`** — semantic search via `EmbeddingService.search`
- **`list_commands`** — browse `Command` records in one directory or all readable directories
- Permission scoping through **`CasbinPermissionService.get_readable_directory_ids`**
- Tool handlers in `mcp/server.py` call services with a per-request SQLAlchemy session

---

## 1. MCP tools vs REST endpoints

| Concern | REST (`/api/v1`) | MCP (`/mcp`) |
|---------|------------------|--------------|
| Transport | HTTP JSON under `/api/v1/...` | JSON-RPC over Streamable HTTP or stdio |
| Auth | `Depends(get_current_user)` | `MCPAuthMiddleware` + `resolve_mcp_user()` |
| Schema | Pydantic response models | Tool return values → JSON-serializable dicts |
| Business logic | `KnowledgeNeuronService`, `EmbeddingService`, … | **Same services** |

Controllers stay thin on REST; MCP tools are equally thin — they should not duplicate SQL or Casbin rules.

---

## 2. Tool scoping — Casbin READ directories

Both tools enforce the same rules as the REST API:

- **Admins** (`users.role == admin`): `get_readable_directory_ids` returns `None` → search/list across all directories
- **Regular users**: only directories with explicit Casbin `READ` (or inherited `WRITE`/`MANAGE`) policies

`list_commands(directory_id=...)` performs an explicit `check_directory_permission(..., READ)` before listing a single folder.

This mirrors `GET /api/v1/knowledge-neurons?search_term=...` and directory-scoped command routes from Weeks 9–10.

---

## 3. Context windows — why search returns top-k

Language models have finite **context windows**. Dumping every `KnowledgeNeuron` into the agent would:

- Exceed token limits
- Dilute relevance (needle-in-haystack problem)
- Cost more per request

`search_knowledge_neurons(query, limit=10)`:

1. Embeds the query (Redis-cached when possible)
2. Runs pgvector cosine similarity
3. Returns only the **top-k** matches inside allowed directories

Agents should search first, then optionally call `get_project_context` (Week 14) for structured project trees the user explicitly exposed.

---

## Tool reference

### `search_knowledge_neurons`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Natural-language search text |
| `limit` | int | 10 | Max results (clamped 1–50) |

Returns: `[{ id, directory_id, title, content, metadata, similarity }]`

### `list_commands`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `directory_id` | string (UUID) | optional | Scope to one folder; omit for all readable directories |

Returns: `[{ id, directory_id, title, content, metadata }]`

---

## Code Walkthrough

```text
mcp/server.py
  search_knowledge_neurons()
    → resolve_mcp_user()
    → CasbinPermissionService.get_readable_directory_ids(user)
    → EmbeddingService.search(...)

  list_commands()
    → resolve_mcp_user()
    → CommandService.list_by_directory() OR list_in_directories()
```

`CommandService.list_in_directories` (new in Week 13) centralizes multi-directory listing for MCP and keeps SQL out of the tool handler.

---

## Further Reading

- [Week 09 — Vector search](./09-vector-search-pgvector.md)
- [Week 10 — Command CRUD](./10-reusing-domain-patterns.md)
- [MCP tools concept](https://modelcontextprotocol.io/docs/concepts/tools)

---

## Exercises (Optional)

1. Add an optional `directory_id` filter to `search_knowledge_neurons` for folder-scoped search.
2. Return command `metadata` keys only (omit full `content`) when the agent only needs titles for disambiguation.
