# AI Revenue Recovery

> **Find revenue that's slipping away and win it back.**

An AI-powered revenue recovery platform that doesn't just send generic payment
reminders. It **detects** revenue at risk, **diagnoses** why, **predicts** the
probability of recovery, **decides** the best intervention, **validates** it
against deterministic business guardrails, **executes** it, and **measures** the
actual money recovered.

Built for the **Razorpay Buildathon** and runs safely in **Razorpay Test Mode**.

---

## Table of contents

- [Problem](#problem)
- [Solution](#solution)
- [Key differentiator](#key-differentiator)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start-90-seconds)
- [Environment variables](#environment-variables)
- [Razorpay setup](#razorpay-setup)
- [Webhook setup](#webhook-setup)
- [Running the backend](#running-the-backend)
- [Running the frontend](#running-the-frontend)
- [Database setup](#database-setup)
- [Deployment (Vercel)](#deployment-vercel)
- [Security](#security)
- [Demo flow (3–5 min)](#demo-flow-35-minutes)
- [AI decision engine](#ai-decision-engine)
- [Guardrails](#guardrails)
- [API reference](#api-reference)
- [Project structure](#project-structure)
- [Future improvements](#future-improvements)

---

## Problem

Revenue loss is **not one single event**. It happens across:

- **Failed payments** — a payment was attempted but declined.
- **Checkout abandonment** — the customer showed intent but didn't complete.
- **Subscription failures** — a recurring charge failed.
- **Overdue invoices** — a receivable crossed its due date.

Generic "payment failed → send reminder" systems treat all of these the same and
burn customer goodwill on cases that will never recover — while under-serving the
high-value cases that would.

## Solution

Every revenue-loss event gets an **AI-generated recovery strategy** based on
context: failure reason, transaction value, customer history, behaviour, and an
explainable **recovery-probability** prediction. The AI can choose to:

`RETRY_PAYMENT` · `PAYMENT_LINK` · `ALTERNATE_PAYMENT_METHOD` · `EMAIL` ·
`WHATSAPP` · `HUMAN_ESCALATION` · `SCHEDULE_RETRY` · **`DO_NOTHING`**

**`DO_NOTHING` is a first-class decision** — when the expected recovery value is
too low to justify the cost/annoyance of intervening, standing down is the
value-maximising choice. This is the core difference from a reminder engine.

## Key differentiator

> **AI decides. Rules control. System executes.**

The LLM never has unrestricted authority over financial actions. It produces a
**structured recommendation**, which is validated against a strict schema and
then a **deterministic guardrail engine**. Only an approved action is executed.

```
LLM / heuristic → strict Pydantic schema → Guardrail engine → Execute
                                                 │
                                            Allowed? ── No ──► Block / downgrade + audit
                                                 │
                                                Yes ──────────► Channel dispatch (test-mode / simulated)
```

## Architecture

```mermaid
flowchart TD
    A[Razorpay Test Payment Event] -->|webhook| B[Revenue Risk Detection]
    B --> C[Root Cause Analysis]
    C --> D[Recovery Probability - logistic regression]
    D --> E[AI Recovery Decision - LLM or heuristic]
    E --> F{Guardrail / Policy Engine}
    F -- Rejected --> G[Audit log + Do Nothing / Block]
    F -- Approved --> H[Recovery Action]
    H --> I[Monitor Result]
    I --> J{Recovered?}
    J -- Yes --> K[Revenue Recovered + Learn]
    J -- No --> L[Failed / Retry within guardrails]
    K --> M[Analytics + Audit Trail]
    L --> M
```

The core product loop:

```
DETECT → UNDERSTAND → PREDICT → DECIDE → VALIDATE → RECOVER → MEASURE → LEARN
```

## Tech stack

| Layer        | Technology |
|--------------|------------|
| Backend      | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| Database     | SQLite (local, zero-setup) or PostgreSQL (deployment) |
| ML           | Explainable logistic regression — trained offline with scikit-learn, served as pure Python |
| AI decisions | OpenAI **or** Anthropic (auto-detected from the key) + deterministic heuristic fallback |
| Payments     | Razorpay (Test Mode) + signed webhooks |
| Frontend     | Next.js 14 (App Router), React, TypeScript, Tailwind CSS, Recharts, lucide-react |
| Deployment   | Vercel — one project, two services (see [Deployment](#deployment-vercel)) |

The recovery model is a `StandardScaler` + `LogisticRegression` pipeline. Its
fitted parameters are exported to `backend/app/ml/model_params.json` and scored
at runtime with plain arithmetic, so scikit-learn, scipy and numpy are **not**
runtime dependencies. That keeps the deployed function small and cold starts
fast, and the scores are numerically identical to the scikit-learn pipeline.

## Quick start (90 seconds)

No credentials required — the app runs fully self-contained (SQLite + simulated
Razorpay + heuristic AI). You need **Python 3.12** and **Node 18+**.

**1. Backend**

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API boots at `http://localhost:8000` (docs at `/docs`), auto-creates the
SQLite DB, loads the recovery model, and seeds realistic demo data on first run.

**2. Frontend** (in a second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** — that's the only URL you need. In development the
Next server proxies `/api` to the backend, so the whole product is served behind
one link, exactly as it is in deployment. To point at a backend on a non-default
port, set `BACKEND_ORIGIN` in `frontend/.env.local` (see `.env.local.example`).

## Environment variables

Copy `.env.example` → `.env` (repo root). All values are optional; sensible
defaults keep the app runnable with zero configuration. See `.env.example` for
the full annotated list. Highlights:

| Variable | Purpose | Default |
|----------|---------|---------|
| `ADMIN_TOKEN` | Guards the test-email endpoint via `X-Admin-Token`. **Required on a public deployment** — unset, that endpoint fails closed there | unset (open locally) |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Real Razorpay **Test** API calls | simulated |
| `RAZORPAY_WEBHOOK_SECRET` | Verify webhook signatures (HMAC-SHA256) | unverified locally |
| `DATABASE_URL` | Any SQLAlchemy URL | `sqlite:///./ai_revenue_recovery.db` |
| `LLM_API_KEY` / `LLM_MODEL` | OpenAI or Anthropic decision engine (`LLM_PROVIDER=auto` detects) | heuristic engine |
| `RESEND_API_KEY` / `EMAIL_FROM` | Real transactional email; unset **blocks** EMAIL actions rather than faking them | email off |
| `MIN_RECOVERY_PROBABILITY` | Guardrail: below this → `DO_NOTHING` | `0.15` |
| `MAX_PAYMENT_RETRIES` | Guardrail: retry cap | `2` |

Secrets are read only from the environment, never hardcoded, never logged, and
`RAZORPAY_KEY_SECRET` is never exposed to the frontend.

## Razorpay setup

1. Create a Razorpay account and switch the dashboard to **Test Mode**.
2. Settings → API Keys → **Generate Test Key**. Put the key id/secret in `.env`.
3. (Optional) Set up a webhook (below).

With credentials present, the app makes **real Razorpay Test API calls** for
orders and payment links, and the UI labels them **`REAL RAZORPAY TEST EVENT`**
vs **`SIMULATED RECOVERY ACTION`**. It never claims a simulated payment was a
real capture.

## Webhook setup

Endpoint: `POST /api/webhooks/razorpay`

1. Expose your local backend (e.g. `ngrok http 8000`).
2. In the Razorpay dashboard → Webhooks, add
   `https://<your-tunnel>/api/webhooks/razorpay`.
3. Set a secret and put it in `.env` as `RAZORPAY_WEBHOOK_SECRET`.
4. Subscribe to `payment.failed`, `payment.captured`, `order.paid`,
   `payment_link.paid`.

The endpoint **verifies the signature** (HMAC-SHA256) before processing, is
**idempotent** (no duplicate cases for repeated events), and on a
`payment.captured` for a tracked transaction it **marks the case recovered and
stops the active workflow**.

## Running the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Useful scripts (run from `backend/` with the venv active):

```bash
python -m scripts.seed          # regenerate demo data
python tests/test_smoke.py      # end-to-end smoke test of the whole API
python tests/test_email.py      # email path only (needs Resend configured)

# Retraining needs the dev extras (scikit-learn + numpy); it rewrites
# app/ml/model_params.json, which the runtime then serves as pure Python.
pip install -r requirements-dev.txt
python -m scripts.train_model
```

## Running the frontend

```bash
cd frontend
npm run dev      # dev server on http://localhost:3000
npm run build && npm start   # production build
```

## Database setup

**SQLite (local default):** nothing to do — the file is created automatically.

**PostgreSQL (required for deployment, optional locally).** A serverless
filesystem cannot persist SQLite between requests, so any deployment needs
Postgres. Set `DATABASE_URL` and the app does the rest:

```bash
# Local Postgres, for parity with production:
docker compose up -d
# in .env:
# DATABASE_URL=postgresql://revenue:revenue@localhost:5432/revenue_recovery
```

`psycopg[binary]` is already in `requirements.txt`. The `postgres://` and
`postgresql://` URL forms that Neon, Supabase and Vercel Postgres hand out are
rewritten to `postgresql+psycopg://` automatically, so you can paste a provider
connection string unchanged.

Tables are created on the first request that touches the database, and an empty
database is seeded with demo data once (guarded by a Postgres advisory lock, so
concurrent cold starts cannot double-seed).

## Demo flow (3–5 minutes)

1. **Landing** (`/`) — the pitch and the recovery loop.
2. **Command Center** (`/command-center`) — headline revenue at risk / recovered
   / recovery rate, the AI action mix, and top recovery opportunities.
3. **Recovery Cases** (`/cases`) — filter and scan every case with its risk,
   recovery probability, and AI-recommended action.
4. **Case detail** — open a case: transaction, customer behaviour, AI analysis,
   the **"Why did the AI choose this?"** explainability, and the recovery
   timeline. Click **Execute Recovery Action** to run guardrails → dispatch →
   measured outcome, and watch revenue recovered update.
5. **Simulation** (`/simulation`) — click **Run Recovery Simulation** to push
   1,000 synthetic cases through the full pipeline; every metric is computed live.
6. **Analytics** (`/analytics`) — intervention performance, funnel, risk mix,
   and the recovery-memory learning table.
7. **Audit Trail** (`/audit`) — every decision, guardrail check, and action.

## AI decision engine

- **Input:** structured features (amount, method, failure reason, customer
  history, recovery probability, recovery-memory best action, etc.).
- **Recovery probability:** an explainable scikit-learn Logistic Regression
  trained on labelled synthetic data, returning a calibrated probability plus
  per-feature contributions. `Expected Recovery Value = Amount × Probability`.
- **Decision:** with `LLM_API_KEY` set, the LLM (OpenAI or Anthropic, auto-detected)
  proposes the action; its output is **merged onto a validated heuristic baseline**
  with strict coercion, so the model enriches the decision but can never emit an
  invalid or unbounded action. Without a key, the heuristic *is* the engine —
  and it is genuinely context-aware (transient failures → retry, expired card →
  alternate instrument, abandonment → gentle nudge + link, low expected value →
  `DO_NOTHING`, large uncertain amounts → human escalation).
- The **ML probability is always authoritative** for the number shown; the LLM
  reasons about it but cannot override it.

## Guardrails

A dedicated deterministic policy engine validates every recommendation before
execution:

- payment already succeeded → **stop**
- case already closed → **stop**
- recovery window elapsed → **stop**
- recovery probability `< MIN_RECOVERY_PROBABILITY` → **downgrade to `DO_NOTHING`**
- customer opted out → **block outbound messaging**
- max retries reached → **downgrade to payment link**
- max messages reached → **block**

Every block/downgrade writes an **audit log**.

## API reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health + model status |
| GET | `/api/config` | Mode, feature flags, policy config |
| GET | `/api/dashboard` | Command-center / overview metrics |
| GET | `/api/recovery-cases` | List cases (filters, search, pagination) |
| GET | `/api/recovery-cases/{id}` | Case detail (+ timeline, explainability) |
| POST | `/api/recovery-cases/{id}/analyze` | Re-run AI analysis |
| POST | `/api/recovery-cases/{id}/execute` | Guardrails → execute → measure |
| GET | `/api/analytics` | Intervention performance, funnel, memory |
| POST | `/api/simulation/run` | Batch simulation (metrics computed live) |
| GET | `/api/audit-logs` | Audit trail |
| POST | `/api/webhooks/razorpay` | Signed Razorpay webhook receiver |
| POST | `/api/settings/email/test` | 🔒 Send a real test email |

Interactive docs: `http://localhost:8000/docs`.

🔒 = requires the `X-Admin-Token` header — see [Security](#security).

## Security

| Concern | How it's handled |
|---------|------------------|
| Secrets | Read from the environment only; never hardcoded, never logged, never sent to the browser. There are no `NEXT_PUBLIC_*` variables, so no key can reach the client bundle. |
| No destructive endpoints | There is no HTTP route that wipes or reseeds the database. Seeding happens on first request (`bootstrap.ensure_ready`) or from the `scripts/seed.py` CLI, so a deployed instance exposes no way to destroy its own data. |
| Paid endpoints | `/api/settings/email/test` sends real mail from a verified sender domain, so it requires `X-Admin-Token`. On a public deployment with `ADMIN_TOKEN` unset it **fails closed** rather than becoming an anonymous mail relay. The token is pasted in Settings and held for the browser session only, never bundled into the app; until one is entered the UI explains why the send is unavailable instead of offering a control that can only 401. |
| Webhook authenticity | HMAC-SHA256 over the raw body, compared with `hmac.compare_digest` (constant time). Invalid signatures are rejected and audited. With no secret configured, a public deployment refuses webhooks entirely — otherwise anyone could forge a capture and fake recovered revenue. |
| SQL injection | All queries go through the SQLAlchemy ORM. The only raw SQL is a literal `SELECT 1` health probe and a parameterised advisory lock. |
| XSS | React escapes by default; the app contains no `dangerouslySetInnerHTML`, `innerHTML` or `eval`. |
| LLM output | Never trusted or executed. Actions are coerced to a known enum, strings truncated, numbers clamped to fixed ranges, and the ML recovery probability stays authoritative. Any malformed response falls back to the deterministic heuristic, then the guardrail engine still runs. |
| PII in logs | Recipient addresses are masked (`j****@example.com`) in logs, audit entries and API responses. |
| CORS | Defaults to localhost only. Deployment is same-origin so CORS is unused; a wildcard origin automatically disables credentialed requests. |
| Error responses | Unhandled exceptions return a generic 500; stack traces stay in the server log. |

Generate an admin token with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then call the guarded endpoint with it:

```bash
curl -X POST https://<your-app>/api/settings/email/test   -H "X-Admin-Token: <token>" -H "Content-Type: application/json"   -d '{"to":"you@example.com"}'
```

## Project structure

```
Ai_Revenue_Recovery/
├── backend/                    # "api" service — FastAPI, mounted at /api
│   ├── app/
│   │   ├── api/                # FastAPI routers
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas (incl. strict AIDecision)
│   │   ├── services/           # orchestration, analytics, simulation, webhooks
│   │   ├── agents/             # decision engine (LLM + heuristic), root cause
│   │   ├── ml/                 # model params (JSON) + features + synthetic data
│   │   ├── policies/           # guardrail engine
│   │   ├── integrations/       # Razorpay, Resend email, channel dispatch
│   │   ├── seed/               # regenerable demo data
│   │   ├── bootstrap.py        # one-time schema init + first-run seeding
│   │   ├── database.py         # engine, session, serverless-aware pooling
│   │   └── main.py             # ASGI entrypoint (`app.main:app`)
│   ├── scripts/                # seed + train_model
│   ├── tests/                  # runnable smoke tests
│   ├── requirements.txt        # runtime deps (no scikit-learn/numpy)
│   └── requirements-dev.txt    # + scikit-learn/numpy for retraining
├── frontend/                   # "web" service — Next.js
│   ├── app/                    # App Router pages
│   ├── components/             # UI, charts, layout, shared
│   ├── lib/                    # api client, types, formatting
│   └── public/                 # hero video
├── vercel.json                 # service definitions + routing
├── .env.example
├── docker-compose.yml          # optional local PostgreSQL
└── README.md
```

## Deployment (Vercel)

The repo deploys as **one Vercel project containing two services**, defined in
`vercel.json`:

| Service | Root | What it is |
|---------|------|------------|
| `web` | `frontend/` | Next.js app, serves everything except `/api` |
| `api` | `backend/` | FastAPI app (`app.main:app`), serves `/api/*` |

Vercel's top-level rewrites route `/api/*` to `api` and everything else to
`web`, so the whole product sits behind **one domain with no CORS and no extra
hop**. The `api` service receives the original path (`/api/dashboard` arrives as
`/api/dashboard`), which is why FastAPI keeps its `/api` prefix.

The `web` service declares a **service binding** to `api`, so server-rendered
pages call the API over Vercel's internal network. That skips Deployment
Protection — a public round-trip would be rejected with a 401 on protected
preview deployments — and is deployment-aware, so each preview talks to its own
API rather than production's.

**Steps**

1. Create a Postgres database (Neon, Supabase or Vercel Postgres) and copy its
   **pooled** connection string. Serverless functions open many short-lived
   connections and will exhaust a direct endpoint.
2. Import the repository on Vercel. `vercel.json` is picked up automatically —
   do not set a Root Directory, since the services define their own.
3. Add the environment variables from `.env.example` to the project. Only
   `DATABASE_URL` is strictly required; without the optional keys the app runs
   with simulated Razorpay and the heuristic decision engine.
4. Deploy. The first request creates the schema and seeds demo data. To reseed
   later, run `python -m scripts.seed` against the same `DATABASE_URL` — there is
   deliberately no HTTP route that can wipe a deployed database.

Run the whole thing locally exactly as Vercel does with `vercel dev`.

> **If Services is unavailable on your plan**, the same layout also deploys as
> two ordinary Vercel projects: one with Root Directory `frontend/`, one with
> `backend/` (auto-detected as FastAPI from `app/main.py`). Delete `vercel.json`
> and set `BACKEND_ORIGIN` on the frontend project to the backend project's URL
> — `lib/api.ts` and `next.config.js` already honour it. The trade-off is two
> deployments and a public hop between them.

## Future improvements

- Reinforcement-learning recovery policy on top of the memory layer.
- Real dunning schedules for subscription failures.
- Live A/B testing of interventions with uplift measurement.
- WhatsApp Business + provider-backed email delivery.
- Multi-tenant auth and per-merchant policy configuration.

---

*Demo data is clearly labelled synthetic. Optional integrations degrade
gracefully when unconfigured — email actions are blocked rather than faked, and
Razorpay calls are labelled SIMULATED without credentials. The app never
performs real-money transactions.*
