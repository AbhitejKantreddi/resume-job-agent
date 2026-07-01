# Agentic Resume & Job-Match Assistant

Upload a resume → an AI agent parses it, searches **live** job postings, scores
skill gaps, rewrites the resume for the best match, and drafts a tailored cover
letter — all as a **visible, multi-step run**, not a single LLM call.

---

## ⚠️ One architectural decision (read this first)

The build spec describes Gumloop as a node-based *visual workflow builder* that
the backend triggers via a webhook (`GUMLOOP_WEBHOOK_URL`). That reflects an
older understanding of the product — **Gumloop today is an agent-first
platform**, so there is no separate webhook-triggered "6-node flow" to stand up.

To keep this project **actually runnable and deployable end-to-end**, the six
nodes from Section 5 of the spec are implemented **in-process inside the FastAPI
backend** (`backend/app/agent/`), one function per node, with the *exact* system
prompts from the spec preserved verbatim in `backend/app/agent/prompts.py`. The
backend streams each node's status to the UI over Server-Sent Events, which
gives you the same visible step-by-step "reasoning" the spec asks for — without
depending on an external orchestrator that doesn't work the way the spec assumes.

Everything else matches the spec: same endpoints, same node prompts, same UI
components, same tech stack.

---

## What it does

1. **Resume Parser** — extract structured JSON from the resume (Groq)
2. **Skill & Role Analyzer** — top skills, target job titles, seniority (Groq)
3. **Job Search** — live web search per target title (Tavily) + structuring (Groq)
4. **Skill Gap Analyzer** — match score + missing/matching skills per job (Groq)
5. **Resume Rewriter** — tailored summary + before/after bullets for the top match (Groq)
6. **Cover Letter Generator** — a specific 3-paragraph cover letter (Groq)

## Architecture

```
Next.js UI (Vercel)  ──HTTP──▶  FastAPI backend (Railway/Render)
      ▲                              │
      │  Server-Sent Events          ├─▶ Groq API        (LLM reasoning, nodes 1,2,3-post,4,5,6)
      └──────────────────────────────┤─▶ Tavily API      (live job search, node 3)
                                      └─▶ reportlab       (resume / cover-letter PDF)
```

The 6-node pipeline runs inside the FastAPI backend (`backend/app/agent/pipeline.py`).

## Tech stack

| Layer          | Choice                                   |
|----------------|------------------------------------------|
| Frontend       | Next.js 14 (App Router) + TS + Tailwind  |
| Backend        | FastAPI (Python 3.11+)                    |
| LLM            | Groq (Llama 3.x, OpenAI-compatible API)                    |
| Web search     | Tavily API                               |
| PDF parsing    | pdfplumber                               |
| PDF generation | reportlab                                |
| Deployment     | Vercel (frontend) + Railway (backend)    |

---

## Setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your keys (see below)
uvicorn app.main:app --reload --port 8000
```

`.env` variables:

| Variable          | Required | Notes                                                     |
|-------------------|----------|-----------------------------------------------------------|
| `GROQ_API_KEY`  | for live | https://console.groq.com/keys                    |
| `GROQ_MODEL`    | no       | defaults to `llama-3.3-70b-versatile`                            |
| `TAVILY_API_KEY`  | for live | https://tavily.com                                        |
| `DEFAULT_LOCATION`| no       | defaults to `Remote`                                      |
| `FRONTEND_ORIGINS`| no       | CORS allow-list, defaults to `http://localhost:3000`      |

> **Demo mode:** with no `GROQ_API_KEY`, the backend returns realistic sample
> data so the full pipeline + UI run end-to-end without any keys. Add the keys
> for real parsing, live job search, and real rewrites.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local     # set NEXT_PUBLIC_API_URL to your backend URL
npm run dev                          # http://localhost:3000
```

---

## Running locally (end-to-end)

1. Start the backend on `:8000`.
2. Start the frontend on `:3000`.
3. Open http://localhost:3000, upload a resume PDF, watch the live run, download
   the tailored resume + cover letter.

Quick backend self-test (no keys needed):

```bash
cd backend && python smoke_test.py
```

---

## API endpoints (Section 6)

| Method | Path                      | Purpose                                    |
|--------|---------------------------|--------------------------------------------|
| POST   | `/api/upload-resume`      | PDF → `{ resume_id, raw_text }` (pdfplumber)|
| POST   | `/api/run-agent`          | start pipeline → `{ run_id }`              |
| GET    | `/api/run-stream/{id}`    | **SSE** stream of live node status         |
| GET    | `/api/run-status/{id}`    | current node status (polling alternative)  |
| GET    | `/api/run-result/{id}`    | final JSON for all six nodes               |
| POST   | `/api/generate-pdf`       | render tailored resume or cover-letter PDF |

> The spec listed SSE on `POST /api/run-agent`; because browsers' `EventSource`
> only supports GET, the live stream is served from `GET /api/run-stream/{id}`.
> `run-agent` kicks off the run and returns the `run_id` the stream uses.

---

## Deployment

**Backend (Railway/Render):** root dir `backend`, start command
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`, env vars `GROQ_API_KEY`,
`TAVILY_API_KEY`, `FRONTEND_ORIGINS` (your Vercel URL).

**Frontend (Vercel):** root dir `frontend`, env var `NEXT_PUBLIC_API_URL`
(your deployed backend URL). Deploy.

Test on the live URLs before recording the demo.

Deployment links (fill in after deploying):
- Frontend: `<your-vercel-url>`
- Backend: `<your-railway-url>`

---

## Agent workflow explanation

The six nodes live in `backend/app/agent/`:
- `prompts.py` — the six system prompts, verbatim from the spec
- `groq_client.py` — Groq wrapper that always returns parsed JSON
- `tavily_client.py` — live web search
- `pipeline.py` — orchestrates the six nodes and reports per-node status
- `mock_data.py` — deterministic sample outputs for demo mode

## Known limitations / future work

- **Run history**: runs are stored in memory; add Supabase/Postgres to persist.
- **Auth**: no user accounts yet.
- **Job sources**: single web-search provider (Tavily); could add LinkedIn/Greenhouse APIs.
- **ATS scoring**: add a keyword-density / ATS-compatibility score.
- **Resilience**: add retries/backoff around Groq + Tavily calls.
