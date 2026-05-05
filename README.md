# AI Underwriting System

Enterprise-grade multi-agent AI system for insurance underwriting. Built with Python, LangGraph, Claude (Anthropic), FastAPI, PostgreSQL, and Streamlit.

Developed by **Raj Kumar** — Lead Developer, QBE Insurance NZ — as a portfolio project targeting senior AI engineering roles.

---

## What This System Does

A broker submits an insurance document. The system autonomously:

1. **Extracts and validates** structured data from broker documents (LLM + prompt-injection detection)
2. **Retrieves claims history** via RAG over historical data (pgvector similarity search)
3. **Evaluates property and environmental hazards** (NZ seismic/flood, AU bushfire/cyclone)
4. **Synthesises a risk decision** — deterministic pre-screen rules, then Claude Sonnet reasoning
5. **Routes referred cases** to a human underwriter queue with SLA management
6. **Calculates premium** using market rate tables with loadings and discounts
7. **Validates the entire chain** through a governance gate before policy issuance

Every LLM call is costed, every decision is auditable, every prompt is versioned.

---

## Architecture

```
BROKER submits document
  ↓
POST /api/v1/submissions/pipeline
  ↓
document_ingestion_agent          Claude Haiku  — extract + sanitise + flag anomalies
  ↓
LangGraph workflow starts
  ↓ ─────────────── parallel via asyncio.gather ───────────────
claims_history_agent              Claude Haiku  — RAG: customer history or benchmark
hazard_evaluation_agent           Claude Sonnet — NZ/AU geo/environmental risk scoring
  ↓ ─────────────── both complete ─────────────────────────────
underwriting_risk_agent           Claude Sonnet — pre-screen rules → synthesise → ACCEPT/DECLINE/REFER
  ↓
  ├─ DECLINE ──────────────────→ decline_node → workflow_status = DECLINED
  ├─ ACCEPT (confidence ≥ 0.70) → auto_approve → pricing_agent → governance_agent → COMPLETED
  └─ REFER / low confidence ──→ human_review_node → interrupt() → workflow_status = AWAITING_HUMAN
                                        ↓
                                POST /api/v1/queue/{id}/decision
                                        ↓
                                resume_pipeline() → pricing_agent → governance_agent
                                        ↓
                                workflow_status = COMPLETED | AWAITING_SENIOR_REVIEW

Cross-cutting (every agent):
  cost_tracking      — token cost recorded in cost_ledger after each LLM call
  governance_agent   — final consistency + compliance + fraud signal check
  prompt_registry    — versioned prompts rendered with per-call context variables
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph (StateGraph, MemorySaver, interrupt/resume) |
| LLM | Claude Haiku 4.5 + Claude Sonnet 4.6 (Anthropic SDK) |
| API | FastAPI 0.115+ · Pydantic v2 |
| Database | PostgreSQL 17 + pgvector (HNSW index, 384-dim embeddings) |
| ORM | SQLAlchemy 2.0 async (`mapped_column` / `Mapped`) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, free) |
| Caching / queues | Redis 7 |
| OCR | Azure Document Intelligence |
| Observability | OpenTelemetry + structlog + Azure Monitor |
| UI | Streamlit (underwriter queue + cost dashboard) |
| Package manager | uv |
| Infrastructure | Docker Compose → Azure Container Apps |

---

## Agents

| Agent | Model | Purpose | Output Schema |
|---|---|---|---|
| Document Ingestion | Haiku 4.5 | Extract structured data; detect prompt injection | `SubmissionData` |
| Claims History | Haiku 4.5 | RAG over customer/benchmark claims | `ClaimProfile` |
| Hazard Evaluation | Sonnet 4.6 | NZ/AU property & environmental risk | `HazardScore` |
| Underwriting Risk | Sonnet 4.6 | Pre-screen rules + LLM synthesis → decision | `RiskAssessment` |
| Pricing | Haiku 4.5 | Market rate tables + loadings/discounts | `PricingOutput` |
| Governance | Sonnet 4.6 | Final consistency + compliance gate | `GovernanceDecision` |

### Deterministic Pre-screen Rules (fire before any LLM call)

| Condition | Decision |
|---|---|
| `hazard_level == EXTREME` **and** `claims_3yr > 2` | Auto-DECLINE |
| `FRAUD_SUSPICION` in risk flags | Auto-DECLINE |
| `sum_insured > NZD/AUD 50,000,000` | Auto-REFER |
| `data_quality == LOW` | Auto-REFER |
| `hazard_confidence < 0.50` | Auto-REFER |
| `extraction_confidence == low` | Auto-REFER |

---

## Quick Start

**Prerequisites:** Docker Desktop running, Python 3.12+, `uv` installed

```bash
# 1. Clone
git clone https://github.com/rajkumar611/AI_UNDERWRITING_SYSTEMS.git
cd AI_UNDERWRITING_SYSTEMS

# 2. Configure environment
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and AZURE_DOCUMENT_INTELLIGENCE_KEY at minimum

# 3. Start infrastructure
docker compose up postgres redis -d

# 4. Install dependencies
uv sync

# 5. Run database migrations
uv run alembic upgrade head

# 6. Seed the database (15 customers, claims, embeddings, 8 regulations)
uv run python scripts/seed_data.py

# 7. Start the API  (port 8081 — avoids conflicts with other local services)
uv run uvicorn main:app --port 8081 --reload

# 8. Start the Underwriter UI  (separate terminal)
uv run streamlit run streamlit_app.py

# 9. Start the Cost Dashboard  (separate terminal, optional)
uv run streamlit run src/underwriting/platform/cost_tracking/dashboard.py
```

| Service | URL |
|---|---|
| API + Swagger docs | http://localhost:8081/docs |
| Underwriter UI | http://localhost:8502 |
| Cost dashboard | http://localhost:8501 |

---

## API Endpoints

### Health
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns `{ "status": "ok", "version": "1.0.0" }` |

### Submissions  (`/api/v1`)
| Method | Path | Description |
|---|---|---|
| `POST` | `/submissions` | Register a submission record (status: `RECEIVED`) |
| `POST` | `/submissions/ingest` | Run document ingestion agent only |
| `GET` | `/submissions/{id}` | Get submission with extracted data, confidence, anomalies |
| `POST` | `/submissions/pipeline` | **Full pipeline** — ingest → claims → hazard → risk → price → govern |

### Underwriter Queue  (`/api/v1`)
| Method | Path | Description |
|---|---|---|
| `GET` | `/queue` | List all `PENDING` queue items, sorted by SLA deadline |
| `GET` | `/queue/{queue_id}` | Get queue item with full submission details |
| `POST` | `/queue/{queue_id}/decision` | Submit underwriter decision and resume the LangGraph pipeline |

**Queue decision actions:** `APPROVE` · `APPROVE_WITH_CONDITIONS` · `OVERRIDE` · `DECLINE` · `REQUEST_MORE_DOCUMENTS` · `REQUEST_MORE_CLAIMS_DATA` · `ESCALATE_TO_SENIOR`

---

## Environment Variables

```bash
# LLM
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_DEFAULT_MODEL=claude-sonnet-4-6

# Database
DATABASE_URL=postgresql+asyncpg://qbe:localdev@localhost:5432/qbe_underwriting

# Redis
REDIS_URL=redis://localhost:6379/0

# Azure Document Intelligence (OCR)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://<resource>.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=...

# Azure Monitor (Observability)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...

# Application
APP_ENV=development
LOG_LEVEL=INFO
SECRET_KEY=change-me-in-production

# LLM cost overrides (USD per 1M tokens — defaults match Anthropic list prices)
CLAUDE_HAIKU_INPUT_COST_PER_1M=0.80
CLAUDE_HAIKU_OUTPUT_COST_PER_1M=4.00
CLAUDE_SONNET_INPUT_COST_PER_1M=3.00
CLAUDE_SONNET_OUTPUT_COST_PER_1M=15.00

# Rate limits
ANTHROPIC_REQUESTS_PER_MINUTE=50
ANTHROPIC_TOKENS_PER_MINUTE=200000

# Human-in-the-loop SLAs
HITL_SLA_STANDARD=14400       # 4 hours (seconds)
HITL_SLA_REFERRED=7200        # 2 hours
HITL_SLA_HIGH_VALUE=3600      # 1 hour

# Underwriting thresholds
HIGH_VALUE_THRESHOLD_NZD=10000000
HIGH_VALUE_THRESHOLD_AUD=10000000
RISK_CONFIDENCE_THRESHOLD=0.70
```

---

## Project Structure

```
AI_UNDERWRTING_SYSTEM/
├── main.py                          ← FastAPI entry point (CORS, lifespan, router wiring)
├── streamlit_app.py                 ← Underwriter UI: Submit · Queue · Submission Lookup
├── pyproject.toml                   ← Dependencies, Ruff, mypy, pytest config
├── docker-compose.yml               ← postgres (pgvector), redis, api, dashboard services
├── Dockerfile
├── alembic.ini
├── .env / .env.example
│
├── src/
│   └── underwriting/
│       ├── api/
│       │   └── routers/
│       │       ├── health.py        ← GET /health
│       │       ├── submissions.py   ← POST/GET /api/v1/submissions
│       │       └── pipeline.py      ← POST /pipeline · GET/POST /queue
│       │
│       ├── pipeline/                ← Business flow (sequential pipeline)
│       │   ├── document_ingestion_agent/    schemas.py · agent.py
│       │   ├── claims_history_agent/        schemas.py · agent.py
│       │   ├── hazard_evaluation_agent/     schemas.py · agent.py
│       │   ├── underwriting_risk_agent/     schemas.py · agent.py
│       │   ├── human_in_the_loop/           schemas.py · agent.py
│       │   └── pricing_agent/               schemas.py · agent.py
│       │
│       └── platform/                ← Cross-cutting infrastructure
│           ├── llm/                 client.py — shared AsyncAnthropic + model routing
│           ├── database/            models.py · connection.py (SQLAlchemy 2.0 async)
│           ├── orchestration/       workflow.py (LangGraph) · prompt_registry.py
│           ├── governance_agent/    schemas.py · agent.py
│           ├── compliance_agent/    schemas.py
│           ├── cost_tracking/       pricing.py · middleware.py · dashboard.py
│           ├── security/            (sanitiser.py — planned)
│           └── observability/       (audit_writer.py — planned)
│
├── alembic/versions/
│   ├── 0001_initial_schema.py
│   ├── 0002_resize_embedding_vector.py   (1536 → 384 dims)
│   ├── 0003_customers_policies_claims.py
│   └── 0004_submission_extracted_data.py
│
├── prompts/                         ← Versioned LLM system prompts (YAML frontmatter + markdown)
│   ├── document_ingestion_agent/v1.0.md
│   ├── claims_history_agent/v1.0.md
│   ├── hazard_evaluation_agent/v1.0.md
│   ├── underwriting_risk_agent/v1.0.md
│   ├── pricing_agent/v1.0.md
│   ├── governance_agent/v1.0.md
│   └── compliance_agent/v1.0.md
│
├── scripts/
│   ├── seed_data.py                 ← 15 customers, claims, embeddings, 8 regulations
│   └── run_ingestion.py             ← Standalone ingestion script
│
├── samples/documents/               ← 4 sample broker docs for testing
│   ├── happy_path.txt
│   ├── high_risk.txt
│   ├── missing_fields.txt
│   └── prompt_injection.txt
│
├── tests/
│   ├── conftest.py
│   ├── api/            test_health.py · test_submissions.py
│   ├── pipeline/       test_schemas.py
│   └── platform/       test_schemas.py
│
└── docs/
    ├── architecture/   end-to-end-flow.md
    └── Q&A/            01–14 interview Q&A (general · architecture · each agent · security · compliance · cost)
```

---

## Running Tests

```bash
uv run pytest                     # all tests
uv run pytest tests/api/          # API tests only
uv run pytest -v --cov=src        # with coverage
```

---

## Key Design Decisions

**Broker documents are untrusted** — prompt-injection detection fires at ingestion; raw text never reaches downstream agents unfiltered.

**Claims and hazard run in parallel** — `asyncio.gather()` inside a single LangGraph node; neither depends on the other, saving ~50% latency on that leg.

**Pricing only runs after human review** — the pricing node is unreachable until an underwriter submits a decision or `auto_approve_node` generates one; no price is ever calculated on an unconfirmed risk.

**Pre-screen rules are deterministic Python** — extreme hazard + high claims count, fraud flags, and out-of-appetite risks are caught before any LLM token is spent.

**Every LLM call is costed and attributed** — `record_llm_cost()` runs after every Anthropic response, recording agent name, prompt version, class of business, jurisdiction, input/output tokens, and `cost_usd` to the `cost_ledger` table.

**Prompts are versioned** — the `PromptRegistry` loads prompts by agent name and active status; prompt version is stored with every cost ledger entry, enabling rollback if a prompt change causes a cost spike or quality regression.

**LangGraph HITL via `interrupt()`** — `human_review_node` calls `interrupt()` to pause the graph; the API stores the thread state in `MemorySaver` keyed by `submission_id`; `resume_pipeline()` injects the underwriter decision and continues from the same node.

**No policy is silently issued** — workflow status must reach `COMPLETED` via the governance gate; any failure sets status to `DECLINED` or `FAILED`.

---

## Jurisdictions

- **NZ** — RBNZ/FMA regulatory rules; NZD pricing; seismic + flood hazard data
- **AU** — APRA regulatory rules; AUD pricing; bushfire + cyclone + flood hazard data

Singapore, MAS, and SGD are out of scope — this system operates in NZ and AU only.

---

## Interview Q&A

Detailed Q&A for every component in [docs/Q&A/](docs/Q&A/) — covering architecture decisions, security design, regulatory compliance, RAG implementation, LangGraph HITL, cost tracking, and production considerations. Written at senior engineering level.
