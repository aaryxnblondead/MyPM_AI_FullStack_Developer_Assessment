# MyPM Fit Check

Fact grounded resume to job matcher with outreach. Core workflow complete.

## Layout

- `frontend/` Next.js App Router with TypeScript and Tailwind v4. Calls backend via `NEXT_PUBLIC_API_URL`.
- `backend/` FastAPI plus SQLite with sqlite-vec. Health at `GET /health`. All LLM calls server side only.
- `docs/` spec PDF, `REQUIREMENTS.md`, `ARCHITECTURE.md` with RAG pipeline, `TEST_REPORT.md` with test results.
- `design/` scraped talentstack.in CSS plus `BRAND.md` tokens.
- `scripts/` helper scripts for local run.

## Setup

1. Backend:
   - `cd backend`
   - `py -m venv .venv`
   - `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
   - Copy `../.env.example` to `../.env` and set `GEMINI_API_KEY`
2. Frontend:
   - `cd frontend`
   - `npm install`
3. Run:
   - Backend: `npm run dev-backend` from repo root (runs on `http://localhost:8000`)
   - Frontend: `npm run dev-frontend` from repo root (runs on `http://localhost:3000`)
   - Tests: `npm run test` from repo root

Backend runs on `http://localhost:8000`. Frontend runs on `http://localhost:3000`.

## Env vars

See `.env.example`. Backend uses `GEMINI_API_KEY`, `LLM_MODEL=gemini-2.5-flash`, `EMBEDDING_MODEL=gemini-embedding-2`, `EMBEDDING_DIM=768`. Frontend uses `NEXT_PUBLIC_API_URL`.

## Testing

### Run all tests
```bash
# Backend tests
cd backend
.\.venv\Scripts\python.exe -m pytest -q

# Frontend lint + types
cd frontend
npm run lint
npx tsc --noEmit
```

### Test scenarios (mocked)
```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_scenarios.py -v
```

### Live evaluation (requires funded GEMINI_API_KEY)
```bash
cd backend
.\.venv\Scripts\python.exe scripts/eval_live.py
```

## Current Status

### Core Workflow ✅ Complete
- All six inputs validate (candidate name, target role, resume text, company name, job title, job description)
- Resume extraction, chunking, embedding into sqlite-vec
- Every match cites retrieved chunks with verified quotes
- Missing requirements show exactly "No evidence found in resume"
- Fit category computed in code, not by LLM (Strong Fit ≥75, Moderate 45-74, Weak <45)
- Explanation and outreach email editable, outreach copyable
- Evaluations persist and reopen from History
- Resumes view at `/resumes` lists every ingested resume with extracted skills, searchable by name, role, or skill
- PDF upload on the analysis form fills the resume textarea (5 MB max, 10 pages, scanned and encrypted PDFs rejected with clear notes)
- Injection scenarios pass (flagged, not inflated, text never used as evidence)
- UI uses extracted talentstack.in tokens throughout

### Known Limitations
- **Gemini API**: Live evaluation requires funded API key (currently returns 402 RESOURCE_EXHAUSTED)
- **Live eval_live.py**: Requires funded API key
- **README**: This document covers setup

### Test Results
See `docs/TEST_REPORT.md` for full scenario breakdown.

## Architecture

- Frontend: Next.js App Router + TypeScript + Tailwind v4
- Backend: FastAPI + Pydantic v2 + SQLAlchemy 2.x + sqlite-vec
- LLM: Google Gemini via `google-genai` SDK
  - `gemini-2.5-flash` for structured extraction, judging, outreach
  - `gemini-embedding-2` for embeddings (768 dim)
- DB: SQLite at `backend/data/app.db` (gitignored), `vec0` virtual table for vectors

## Design Tokens

Extracted from `design/css/` (talentstack.in):
- Primary navy: #113754
- Secondary gray: #666666
- Title: #111111
- Background: #ffffff
- Tint: #eff2e6
- Mist: #e3e7eb
- Fonts: Inter (body), Outfit (headings)
- Radius: pill 50px, card 10px, input 40px

See `design/BRAND.md` and `design/DESIGN_TOKENS.md` for full tables with source refs.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── db.py              # DB connection + sqlite-vec loader
│   │   ├── config.py          # Pydantic settings
│   │   ├── db_init.py         # Explicit vec table creation
│   │   ├── main.py            # FastAPI app + exception handlers
│   │   ├── prompts/           # Versioned prompts (v1)
│   │   ├── routers/           # /api/evaluations, /api/candidates
│   │   └── services/          # Core RAG pipeline
│   ├── tests/                 # 38 tests (unit + scenarios)
│   └── scripts/               # check_vec.py, check_gemini.py, eval_live.py
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   ├── components/ui/     # Primitives (Button, Card, etc.)
│   │   └── lib/api.ts         # Typed API client
├── design/
│   ├── css/                   # 36 scraped CSS files
│   ├── BRAND.md               # Token summary
│   ├── DESIGN_TOKENS.md       # Detailed tables with refs
│   └── design-tokens.json     # Machine-readable tokens
├── docs/
│   ├── REQUIREMENTS.md        # Spec extracted from PDF
│   ├── ARCHITECTURE.md        # RAG pipeline design
│   └── TEST_REPORT.md         # Scenario results
└── scripts/                   # Dev scripts
```

## Commands

```bash
# Root scripts (from repo root)
npm run dev-backend    # Start FastAPI on :8000
npm run dev-frontend   # Start Next.js on :3000
npm run test           # Run all tests (backend + frontend)
```