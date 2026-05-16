# File Structure Prompt

## Prompt

```
You are a senior software architect. Generate a clean, production-ready
file structure for the project described below. Return only the directory
tree with one-line comments explaining each file's responsibility.
No explanation outside the tree.

PROJECT: AI-powered operational assistant for professional services firms
STACK: Next.js (frontend) · FastAPI (backend) · LangGraph (agent) · pgvector (vector DB) · PostgreSQL (state store)

REQUIREMENTS:
- Contract + email ingestion pipeline
- Scope change detection (LLM extraction + rule engine)
- Human approval gate before any tool execution
- Integrations: Jira, Notion, Slack, billing
- Audit log for every agent action

Format:
project-root/
├── frontend/          # Next.js dashboard
│   └── ...
├── backend/           # FastAPI + agent
│   └── ...
└── ...
```

---

## Expected Output (reference)

```
project-root/
├── frontend/                          # Next.js 14 dashboard
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                   # Scope alert feed
│   │   ├── approvals/
│   │   │   └── page.tsx               # PM approval queue
│   │   └── projects/
│   │       └── [id]/page.tsx          # Per-project timeline + billing
│   ├── components/
│   │   ├── ScopeAlertCard.tsx
│   │   ├── ApprovalModal.tsx
│   │   └── TimelineDiff.tsx
│   └── lib/
│       └── api.ts                     # Typed fetch wrappers
│
├── backend/
│   ├── main.py                        # FastAPI entrypoint
│   ├── api/
│   │   ├── ingest.py                  # Webhook: email / file upload
│   │   ├── approvals.py               # PM approve / reject endpoints
│   │   └── projects.py                # Project + baseline CRUD
│   ├── ingestion/
│   │   ├── parser.py                  # Unstructured.io wrapper
│   │   ├── clause_segmenter.py        # Regex + heuristic clause splitter
│   │   ├── ner.py                     # spaCy NER: party · date · $ · scope
│   │   └── chunker.py                 # Clause-aware chunker → pgvector
│   ├── agent/
│   │   ├── graph.py                   # LangGraph state machine definition
│   │   ├── nodes/
│   │   │   ├── retrieve.py            # RAG retrieval from pgvector
│   │   │   ├── extract.py             # Scope change extraction prompt
│   │   │   ├── diff.py                # Compare extracted intent vs baseline
│   │   │   ├── risk.py                # Risk rule engine (no LLM)
│   │   │   └── route.py               # Auto-approve vs flag for PM
│   │   └── prompts/
│   │       └── scope_change.md        # Extraction prompt template
│   ├── executors/                     # Only run after PM approval
│   │   ├── jira.py
│   │   ├── notion.py
│   │   ├── slack.py
│   │   └── billing.py
│   ├── db/
│   │   ├── models.py                  # SQLAlchemy: Project · Baseline · AuditLog
│   │   ├── migrations/                # Alembic migrations
│   │   └── vector.py                  # pgvector insert / similarity search
│   └── core/
│       ├── config.py                  # Env vars (pydantic-settings)
│       ├── audit.py                   # Append-only audit log writer
│       └── schemas.py                 # Pydantic I/O schemas
│
├── infra/
│   ├── docker-compose.yml             # Postgres + pgvector + backend + frontend
│   └── .env.example
│
└── docs/
    ├── scope_change_prompt.md         # Extraction prompt (editable)
    ├── file_structure_prompt.md       # This file
    └── architecture.md               # System overview
```
