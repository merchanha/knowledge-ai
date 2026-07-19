# 10 — Reusing Domain Patterns (Command CRUD)

> **Audience:** Junior Python developers learning AI engineering. Week 10 introduces **Command** — reusable instruction snippets that mirror KnowledgeNeuron CRUD but skip the embedding pipeline.

## What We Built

- **`models/command.py`** — `commands` table: `title`, `content`, `directory_id`, `metadata` (JSONB)
- **`services/command.py`** — `CommandService`: create, read, update, delete, list by directory
- **`schemas/command.py`** — Pydantic DTOs for API request/response
- **`api/v1/commands.py`** — thin REST controllers with Casbin directory permission checks
- **Alembic migration** — `20260704_0001_add_commands_table`
- **Tests** — `tests/test_command.py` (service) + `tests/test_commands_api.py` (HTTP)

Commands deliberately have **no embeddings**. They are listed and fetched by directory path, not searched semantically.

---

## 1. Commands vs KnowledgeNeurons

Both entities live inside directory folders and share the same CRUD shape. The difference is **purpose** and **how agents consume them**:

| Aspect | KnowledgeNeuron | Command |
|--------|---------------|---------|
| Purpose | Stored knowledge documents (notes, runbooks, specs) | Reusable instruction snippets (prompts, checklists, templates) |
| Semantic search | Yes — pgvector + Voyage AI (Weeks 8–9) | No — browse by directory only |
| Embedding column | `embedding vector(1024)` | None |
| Celery task on save | `embed_knowledge_neuron` | None |
| MCP usage (Week 14) | Included in ProjectContext tree + search tool | Listed in ProjectContext tree + list tool |

**Why only neurons get semantic search:** Search answers “find knowledge similar to this question.” Commands are short, procedural snippets you already know where to look — they are organized by folder, not discovered by meaning. Adding embeddings would add cost and complexity without a clear retrieval benefit.

---

## 2. When to duplicate vs abstract

`CommandService` is almost identical to `KnowledgeNeuronService` minus `_enqueue_embed`. You might ask: should we extract a shared `DirectoryContentService` base class?

**Our choice: duplicate (copy the pattern, not a base class).**

| Approach | Pros | Cons |
|----------|------|------|
| **Duplicate** (what we did) | Each domain stays readable; neurons can evolve (embeddings, search) independently; no inheritance coupling | Some repeated validation and CRUD code |
| **Shared base class** | Less duplication | Hides differences; harder to add neuron-only behavior; generic names (`ContentItem`) drift from domain language |
| **Generic CRUD helper** | DRY for simple cases | Loses type safety; metadata/embedding hooks become awkward |

**Rule of thumb:** Duplicate when two things *look* similar today but have **different futures**. KnowledgeNeurons gained embeddings, vector indexes, and search. Commands will stay plain text. A shared abstraction would have fought those changes.

Copy-paste is OK when:
- The duplicated block is small (~100 lines) and stable
- Domain names matter (`Command` vs `KnowledgeNeuron`)
- One copy will diverge (embeddings, MCP tools)

Abstract when:
- Three or more types share identical behavior with no planned divergence
- The shared logic is complex and bug-prone (e.g. tree move algorithms — we did not duplicate `DirectoryService`)

---

## 3. Permission model (same as KnowledgeNeuron)

Permissions are checked on the **parent directory**, not the command id:

| Action | Route | Casbin permission on parent directory |
|--------|-------|--------------------------------------|
| List | `GET /directories/{directory_id}/commands` | `READ` |
| Get one | `GET /commands/{command_id}` | `READ` on command's directory |
| Create | `POST /directories/{directory_id}/commands` | `WRITE` |
| Update | `PATCH /commands/{command_id}` | `WRITE` on command's directory |
| Delete | `DELETE /commands/{command_id}` | `MANAGE` on command's directory |

The `_require_command_directory_permission` helper mirrors `_require_neuron_directory_permission` from Week 7.

---

## 4. Code walkthrough

**Service layer** (`services/command.py`):

1. `create` validates title/content, confirms directory exists via `DirectoryService.require_by_id`
2. Persists `Command` with `metadata_json` mapped to DB column `metadata`
3. No Celery enqueue — save completes synchronously

**Controller layer** (`api/v1/commands.py`):

1. List/create routes use `require_directory_permission` on path `directory_id`
2. Get/update/delete routes load the command first, then check permission on `command.directory_id`

**ORM** (`models/command.py`):

- `Directory.commands` relationship with `cascade="all, delete-orphan"` — deleting a folder deletes its commands (same as neurons)

---

## 5. Further reading

- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) — reusable permission factories
- [SQLAlchemy Relationships](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html) — cascade delete behavior
- Week 7 doc: `07-domain-modeling-patterns.md` — the pattern Commands copied

---

## Exercises (Optional)

1. Add a `GET /commands` route that lists commands across all directories the user can READ (hint: reuse `get_readable_directory_ids` from Casbin).
2. Sketch what a shared `DirectoryDocumentService` would look like — then list three ways KnowledgeNeurons would break out of it by Week 9.
