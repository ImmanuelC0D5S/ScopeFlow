# Handoff Document — AI Operational Assistant
> Trigger: `/handoff` · Generated for: Atigravity AI
> Project: AI-powered operational assistant for professional services firms

---

## 1. Problem Statement

Professional services firms (legal, consulting, accounting, architecture) manage projects across fragmented tools — email, PDFs, Excel, Slack, Jira, Notion, and billing systems. When a client requests a change or adds new requirements, teams manually update tasks, timelines, invoices, and documents across all systems.

**Core pains:**
- Scope creep goes undetected → unbilled work
- Manual updates across 5+ tools → operational overhead
- Billing errors from missed change orders
- Senior staff doing admin instead of billable work

---

## 2. Product Vision

An AI-powered operational assistant that:
1. Reads and understands contracts + client communications
2. Detects scope changes automatically by comparing against original agreed scope
3. Drafts updates across Jira, Notion, Slack, and billing
4. Surfaces them to the PM for one-click approval — never executes autonomously on high-risk actions

---

## 3. Architecture Overview

```
Next.js Dashboard
      ↓
FastAPI Gateway (auth · rate limit · webhook ingestion)
      ↓
Ingestion Pipeline
  ├── Unstructured.io (PDF · DOCX · email → plain text)
  ├── Clause Segmenter (regex + heuristics)
  ├── NER pass (party · date · $ · scope terms)
  └── Chunker → pgvector

LangGraph Agent Orchestrator
  ├── retrieve    → RAG from pgvector
  ├── extract     → LLM scope change extraction (structured JSON)
  ├── diff        → compare vs scope baseline (deterministic code)
  ├── risk        → rule engine (no LLM, thresholds)
  └── route       → auto-approve | flag_for_pm

Human Approval Gate (PM approves/rejects in dashboard)
      ↓
Workflow Executors (only run post-approval)
  ├── Jira
  ├── Notion
  ├── Slack
  └── Billing

Audit Log → Postgres append-only events table
```

**Key architectural decision:** LLM does reading + extraction only. Business logic (risk scoring, routing, execution) runs in deterministic code. This keeps the system auditable and prevents hallucination-driven actions.

---

## 4. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Frontend | Next.js 14 (App Router) | Server components, fast routing |
| Backend | FastAPI | Async, Pydantic-native, fast |
| Agent | LangGraph | Stateful multi-step, native HITL support |
| Vector store | pgvector (Postgres extension) | Avoid second infra footprint |
| Embeddings | text-embedding-3-small | Cheap, fast, 128k context |
| LLM | claude-sonnet-4-20250514 | Long context for full contracts |
| Document parsing | Unstructured.io | Handles PDF, DOCX, EML, Slack export |
| ORM | SQLAlchemy + Alembic | Migrations, type safety |
| Config | pydantic-settings | Env var validation |

---

## 5. File Structure

```
project-root/
├── frontend/
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
│   ├── executors/
│   │   ├── jira.py
│   │   ├── notion.py
│   │   ├── slack.py
│   │   └── billing.py
│   ├── db/
│   │   ├── models.py                  # SQLAlchemy models
│   │   ├── migrations/                # Alembic
│   │   └── vector.py                  # pgvector ops
│   └── core/
│       ├── config.py
│       ├── audit.py                   # Append-only audit log
│       └── schemas.py                 # Pydantic schemas
│
├── infra/
│   ├── docker-compose.yml
│   └── .env.example
│
└── docs/
    ├── scope_change_prompt.md
    ├── file_structure_prompt.md
    └── handoff.md                     # This file
```

---

## 6. Core Data Models

### Scope Baseline (Postgres)
```python
class Deliverable(Base):
    id: str                # e.g. "D1"
    project_id: str
    description: str
    hours: int
    due_date: date
    status: str            # active | completed | disputed

class PaymentMilestone(Base):
    id: str
    project_id: str
    amount: float
    currency: str
    trigger: str           # e.g. "on delivery of D1"
    due_date: date

class Exclusion(Base):
    id: str
    project_id: str
    description: str       # e.g. "mobile app development"
```

### Scope Change Event (Postgres)
```python
class ScopeChangeEvent(Base):
    id: str
    project_id: str
    source: str            # email | slack | amendment
    raw_message: str
    extracted_json: dict   # LLM output
    risk_level: str        # low | medium | high
    status: str            # pending | approved | rejected
    pm_note: str
    created_at: datetime
    resolved_at: datetime
```

### Audit Log (append-only)
```python
class AuditLog(Base):
    id: str
    event_type: str        # scope_detected | pm_approved | jira_updated | ...
    actor: str             # system | pm_user_id
    payload: dict
    timestamp: datetime
    # NO update or delete ever — insert only
```

---

## 7. Scope Change Detection — Key Logic

### LLM Extraction (backend/agent/nodes/extract.py)
- Model: `claude-sonnet-4-20250514`
- Temperature: `0` (deterministic)
- Returns structured JSON — see `docs/scope_change_prompt.md`
- Validated with Pydantic before any downstream use

### Risk Rule Engine (backend/agent/nodes/risk.py)
```python
def apply_risk_rules(extracted: ScopeChangeExtraction) -> str:
    if extracted.type in ("clarification", "admin"):
        return "ignore"
    if extracted.confidence < 0.75:
        return "flag_for_pm"
    if extracted.explicitly_excluded:
        return "flag_for_pm"
    if extracted.new_deliverable:
        return "flag_for_pm"
    if extracted.dollar_impact and extracted.dollar_impact > 5000:
        return "flag_for_pm"
    return "auto_approve"   # only genuinely low-risk changes
```

### Critical rule: executors never run without PM approval
```python
# backend/api/approvals.py
@router.post("/approvals/{event_id}/approve")
async def approve(event_id: str, pm_user: User = Depends(get_current_pm)):
    event = await db.get(ScopeChangeEvent, event_id)
    event.status = "approved"
    event.resolved_at = datetime.utcnow()
    await audit_log("pm_approved", actor=pm_user.id, payload=event.dict())
    await execute_approved_change(event)   # only here
```

---

## 8. MVP Scope (Recommended Build Order)

### Phase 1 — Baseline extraction (no integrations)
- Upload contract PDF → extract scope baseline → display in dashboard
- PM confirms/edits the extracted baseline
- Goal: prove extraction is reliable before building anything else

### Phase 2 — Change detection
- Email webhook → ingestion pipeline → LLM extraction → diff vs baseline
- Show detected changes in dashboard with confidence score + risk level
- PM approves or rejects — no tool execution yet
- Goal: prove detection is accurate enough to trust

### Phase 3 — Execution
- Approved changes push to Jira (task creation/update)
- Draft change order generated for billing
- Slack notification to project team
- Goal: close the loop, demonstrate ROI

---

## 9. Key Prompts (reference)

- Scope change extraction prompt → `docs/scope_change_prompt.md`
- File structure generation prompt → `docs/file_structure_prompt.md`

---

## 10. What Has NOT Been Built Yet

- No code has been written — architecture and prompts only
- No database schema has been migrated
- No LangGraph graph has been implemented
- No frontend exists
- Integration credentials (Jira, Notion, Slack, billing) not configured

---

## 11. Open Decisions

| Decision | Options | Recommendation |
|---|---|---|
| Email ingestion | Webhooks (SendGrid/Postmark) vs Gmail API polling | Webhooks — lower latency |
| Billing integration | Stripe · QuickBooks · custom | Decide based on target customer's existing stack |
| Auth | Clerk · Auth.js · Supabase Auth | Clerk for fastest PM dashboard setup |
| Deployment | Railway · Render · AWS | Railway for MVP speed |
| Multi-tenancy | One DB per firm vs row-level security | RLS on Postgres — simpler to start |

---

*End of handoff. Continue from Phase 1.*
