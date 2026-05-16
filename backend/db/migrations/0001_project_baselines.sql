CREATE TABLE projects (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  total_contract_value NUMERIC(12,2),
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE project_baselines (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id),
  version INT NOT NULL,
  source_doc_id TEXT,
  effective_from DATE,
  effective_to DATE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(project_id, version)
);

CREATE TABLE baseline_deliverables (
  id UUID PRIMARY KEY,
  baseline_id UUID NOT NULL REFERENCES project_baselines(id) ON DELETE CASCADE,
  deliverable_code TEXT NOT NULL,
  description TEXT NOT NULL,
  estimated_hours NUMERIC(8,2),
  due_date DATE,
  status TEXT NOT NULL DEFAULT 'active',
  UNIQUE(baseline_id, deliverable_code)
);

CREATE TABLE baseline_exclusions (
  id UUID PRIMARY KEY,
  baseline_id UUID NOT NULL REFERENCES project_baselines(id) ON DELETE CASCADE,
  description TEXT NOT NULL
);

CREATE TABLE project_contacts (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id),
  channel TEXT NOT NULL,
  sender_key TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(channel, sender_key, project_id)
);

CREATE TABLE thread_project_overrides (
  id UUID PRIMARY KEY,
  channel TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  project_id UUID NOT NULL REFERENCES projects(id),
  set_by_pm_user_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(channel, thread_id)
);

CREATE TABLE unrouted_inbox (
  id UUID PRIMARY KEY,
  channel TEXT NOT NULL,
  sender_key TEXT NOT NULL,
  thread_id TEXT,
  raw_message TEXT NOT NULL,
  candidate_project_ids UUID[] NOT NULL,
  status TEXT NOT NULL DEFAULT 'needs_routing',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  routed_project_id UUID REFERENCES projects(id),
  routed_at TIMESTAMPTZ
);
