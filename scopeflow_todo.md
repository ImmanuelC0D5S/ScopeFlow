# ScopeFlow — Build To-Do List
> AI-powered operational assistant for professional services firms
> 48-hour hackathon build tracker

---

## ✅ Done
- [x] Architecture designed
- [x] File structure defined
- [x] Scope change extraction prompt written (`docs/scope_change_prompt.md`)
- [x] Postgres schema designed (project_contacts, thread_project_overrides, unrouted_inbox)
- [x] DB routing repository implemented (`backend/db/routing_repository.py`)
- [x] Ingest endpoint wired (`POST /ingest/message`)
- [x] PM assignment endpoint wired (`POST /ingest/unrouted/{id}/assign`)
- [x] Schemas defined (`backend/core/schemas.py`)
- [x] Config wired (`backend/core/config.py`)
- [x] Backend compiles and starts (uvicorn on :8001)
- [x] Health check passing (`GET /health → 200`)

---

## 🔴 Blocked (fix first)
- [x] Neon Postgres connected — update DATABASE_URL in infra/.env
- [x] Migration applied — `backend/db/migrations/0001_project_baselines.sql`
- [x] `POST /ingest/message` returns non-503

---

## 🟡 Step 2 — Ingestion Pipeline
- [x] PDF + DOCX parser (Unstructured.io wrapper) → `backend/ingestion/parser.py`
- [x] Clause segmenter (regex + heuristics) → `backend/ingestion/clause_segmenter.py`
- [x] NER pass (party · date · $ · scope terms) → `backend/ingestion/ner.py`
- [x] Clause-aware chunker → `backend/ingestion/chunker.py`
- [x] pgvector setup + embedding insert → `backend/db/vector.py`
- [x] Upload endpoint → `POST /ingest/contract`

---

## 🟡 Step 3 — Scope Baseline Extraction
- [x] LLM extraction call (gemini-1.5-pro-002, temp=0)
- [x] Pydantic validation of LLM output
- [x] Scope baseline written to Postgres (deliverables, milestones, exclusions)
- [x] `GET /projects/{id}/baseline` endpoint returns structured baseline
- [x] PM confirms/edits baseline in dashboard

---

## 🟡 Step 4 — Change Detection Agent (LangGraph)
- [x] LangGraph graph skeleton → `backend/agent/graph.py`
- [x] `retrieve` node — RAG from pgvector
- [x] `extract` node — scope change extraction prompt
- [x] `diff` node — compare extracted intent vs baseline
- [x] `risk` node — rule engine (no LLM)
- [x] `route` node — auto_approve | flag_for_pm
- [x] `POST /ingest/message` triggers agent after routing

---

## 🟡 Step 5 — PM Approval Gate
- [x] Approval queue endpoint → `GET /approvals/pending`
- [x] Approve endpoint → `POST /approvals/{id}/approve`
- [x] Reject endpoint → `POST /approvals/{id}/reject`
- [x] Audit log write on every approval/rejection
- [x] Approved changes trigger executor

---

## 🟡 Step 6 — Executors (post-approval only)
- [ ] Jira executor → `backend/executors/jira.py`
- [ ] Slack executor → `backend/executors/slack.py`
- [ ] Notion executor → `backend/executors/notion.py`
- [ ] Billing draft generator → `backend/executors/billing.py`
- [ ] Audit log write on every execution

---

## 🟡 Step 7 — Frontend (Next.js)
- [ ] Project dashboard → scope alert feed
- [ ] Approval queue UI → `ScopeAlertCard` + `ApprovalModal`
- [ ] Baseline viewer (PM confirms extracted scope)
- [ ] Timeline diff view
- [ ] Unrouted inbox UI (PM assigns ambiguous emails)

---

## 🟢 Demo Path (lock this by hour 40)
- [ ] One real contract PDF uploaded and parsed
- [ ] Scope baseline extracted and displayed
- [ ] One client email triggers scope change detection
- [ ] Change flagged in dashboard with confidence score
- [ ] PM approves in one click
- [ ] Jira epic created + Slack message fired
- [ ] Full flow runs live in under 60 seconds

---

## 📦 Handoff / Docs
- [x] `docs/scope_change_prompt.md`
- [x] `docs/file_structure_prompt.md`
- [x] `docs/handoff.md`
- [ ] `docs/architecture.md` (system diagram)
- [ ] `README.md` with setup instructions
- [ ] `.env.example` updated with all required keys

---

## 🔑 Env Vars Needed
- [ ] `DATABASE_URL` — Neon Postgres connection string
- [ ] `ANTHROPIC_API_KEY` — for LLM extraction calls
- [ ] `JIRA_API_KEY` + `JIRA_BASE_URL`
- [ ] `SLACK_BOT_TOKEN`
- [ ] `NOTION_API_KEY`

---

*Update this file as you go. Paste into Codex with "mark X as done, proceed to Y."*
