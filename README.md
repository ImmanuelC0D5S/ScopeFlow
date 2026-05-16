# ScopeFlow

> AI that detects scope creep in client contracts and automates project updates across your entire stack.

ScopeFlow reads contracts and client communications, detects scope changes automatically, and executes updates across Jira, Slack, and billing — replacing hours of manual work with a single PM approval click.

---

## The Problem

A client emails: *"Can we also add a mobile app version?"*

Someone now has to manually update the contract, add Jira tasks, revise the timeline, raise a change order, and notify the team. Across five different tools. Every single time scope changes.

ScopeFlow fixes that.

---

## How It Works

```
Contract + Client Email
        ↓
Ingestion Pipeline
(parse · segment · embed)
        ↓
LangGraph Agent
(retrieve → extract → diff → risk → route)
        ↓
Human Approval Gate
(PM approves in one click)
        ↓
Executors
(Jira · Slack · Notion · Billing)
```

1. **Upload a contract** — ScopeFlow extracts the scope baseline (deliverables, exclusions, payment milestones)
2. **Client email arrives** — agent reads it, compares against baseline, detects what changed
3. **PM gets a flag** — confidence score, risk level, and a draft of what will be updated
4. **PM approves** — Jira epic created, Slack message sent, change order drafted. Done.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) |
| Backend | FastAPI |
| Agent | LangGraph |
| Vector Store | pgvector (Postgres) |
| LLM | Claude Sonnet (claude-sonnet-4-20250514) |
| Document Parsing | Unstructured.io |
| Database | Neon (serverless Postgres) |
| Embeddings | text-embedding-3-small |

---

## Project Structure

```
scopeflow/
├── frontend/                          # Next.js dashboard
│   ├── app/
│   │   ├── page.tsx                   # Scope alert feed
│   │   ├── approvals/page.tsx         # PM approval queue
│   │   └── projects/[id]/page.tsx     # Per-project view
│   └── components/
│       ├── ScopeAlertCard.tsx
│       ├── ApprovalModal.tsx
│       └── TimelineDiff.tsx
│
├── backend/
│   ├── main.py                        # FastAPI entrypoint
│   ├── api/
│   │   ├── ingest.py                  # Email + file upload webhooks
│   │   ├── approvals.py               # PM approve / reject
│   │   └── projects.py                # Project + baseline CRUD
│   ├── ingestion/
│   │   ├── parser.py                  # Unstructured.io wrapper
│   │   ├── clause_segmenter.py        # Clause splitter
│   │   ├── ner.py                     # Entity extraction
│   │   └── chunker.py                 # Clause-aware chunker
│   ├── agent/
│   │   ├── graph.py                   # LangGraph state machine
│   │   ├── nodes/
│   │   │   ├── retrieve.py            # RAG from pgvector
│   │   │   ├── extract.py             # LLM scope extraction
│   │   │   ├── diff.py                # Baseline comparison
│   │   │   ├── risk.py                # Rule engine
│   │   │   └── route.py               # Approval routing
│   │   └── prompts/
│   │       └── scope_change.md        # Extraction prompt
│   ├── executors/
│   │   ├── jira.py
│   │   ├── slack.py
│   │   ├── notion.py
│   │   └── billing.py
│   ├── db/
│   │   ├── models.py
│   │   ├── routing_repository.py
│   │   ├── vector.py
│   │   └── migrations/
│   └── core/
│       ├── config.py
│       ├── audit.py
│       └── schemas.py
│
├── infra/
│   ├── docker-compose.yml
│   └── .env.example
│
└── docs/
    ├── scope_change_prompt.md
    ├── file_structure_prompt.md
    ├── handoff.md
    └── scopeflow_todo.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- A [Neon](https://neon.tech) Postgres database
- An [Anthropic](https://console.anthropic.com) API key

### 1. Clone the repo

```bash
git clone https://github.com/ImmanuelCOD5S/scopeflow.git
cd scopeflow
```

### 2. Set up environment variables

```bash
cp infra/.env.example infra/.env
```

Fill in:

```env
DATABASE_URL=postgresql://...          # Neon connection string
ANTHROPIC_API_KEY=sk-ant-...
JIRA_API_KEY=...
JIRA_BASE_URL=https://yourorg.atlassian.net
SLACK_BOT_TOKEN=xoxb-...
NOTION_API_KEY=secret_...
```

### 3. Apply migrations

```bash
psql $DATABASE_URL -f backend/db/migrations/0001_project_baselines.sql
```

### 4. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### 5. Install frontend dependencies

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`
Backend runs at `http://localhost:8001`

---

## API Endpoints

### Ingest
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest/message` | Ingest an email or Slack message |
| `POST` | `/ingest/contract` | Upload a contract PDF |
| `POST` | `/ingest/unrouted/{id}/assign` | PM assigns an unrouted message |

### Projects
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/projects` | List all projects |
| `GET` | `/projects/{id}/baseline` | Get scope baseline |
| `POST` | `/projects` | Create a project |

### Approvals
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/approvals/pending` | Get PM approval queue |
| `POST` | `/approvals/{id}/approve` | Approve a scope change |
| `POST` | `/approvals/{id}/reject` | Reject a scope change |

### Health
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |

---

## Key Design Decisions

**LLM does extraction only — not decisions.**
The agent extracts structured facts from communications. Business logic (risk scoring, routing, execution) runs in deterministic Python code. This keeps the system auditable and prevents hallucination-driven actions.

**Nothing executes without PM approval.**
Executors (Jira, Slack, billing) only run after explicit PM approval via the dashboard. Auto-approve is only available for low-confidence, low-dollar, non-excluded changes.

**Scope baseline is structured data, not embeddings.**
The original contract scope is stored as structured records (deliverables, milestones, exclusions) in Postgres — not just embedded text. This enables reliable diffing and rule-based conflict detection.

**Audit log is append-only.**
Every agent action, PM decision, and executor call is logged to an immutable audit trail. No updates or deletes — insert only.

---

## Risk Rule Engine

Applied after every LLM extraction call — in code, not in the prompt:

| Condition | Action |
|---|---|
| `confidence < 0.75` | Always `flag_for_pm` |
| `explicitly_excluded = true` | Always `flag_for_pm` |
| `new_deliverable = true` | Always `flag_for_pm` |
| `dollar_impact > $5,000` | Always `flag_for_pm` |
| `type = clarification` | `ignore` |
| Everything else | `auto_approve` candidate |

---

## Built At

IBM BOP Hackathon · 48 hours · May 2026

**Team**
- Immanuel — Backend · LangGraph agent · ingestion pipeline
- Ashwin — Frontend · BOP integrations · executors

---

## License

MIT
