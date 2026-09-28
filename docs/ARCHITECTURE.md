# Architecture - fact grounded matching

This file is the global context for the build. PDF in `docs/` is still the spec and wins on conflicts.

## Stack fixed

- Frontend: Next.js App Router plus React plus TypeScript plus Tailwind v4.
- Backend: FastAPI plus Pydantic v2. All LLM and embedding calls server side only.
- DB: SQLite with sqlite-vec. SQLAlchemy for tables, `vec0` virtual table for vectors. No pgvector.
- LLM: Google Gemini via `google-genai` SDK 2.25.0 verified here.
  - `gemini-2.5-flash` for extraction, judging, outreach with `response_mime_type="application/json"` plus `response_schema`.
  - `gemini-embedding-2` for embeddings.

## Gemini findings verified 2026-09-28

Embedding model `gemini-embedding-2`:
- GA April 2026. Input token limit 8192.
- Output dim flexible 128 to 3072, default 3072, recommended 768, 1536, 3072. Uses MRL. Non default dims auto normalized.
- `output_dimensionality` param controls size. We default to 3072 (model native output) to avoid truncation surprises. Startup rebuilds the vec table if the configured dim ever changes.
- `task_type` param exists in SDK but docs say do not use it for v2. Use prompt prefixes instead:
  - query: `task: search result | query: {text}` plus variants for QA and fact checking
  - doc: `title: none | text: {chunk}`
  - symmetric only for classification, clustering, sentence similarity
- `EmbedContentConfig` also supports `title`, `mime_type`, `auto_truncate`, `document_ocr`, `audio_track_extraction`.
- Store dim in config `EMBEDDING_DIM` and use it when creating the `vec0` table.

Generation model `gemini-2.5-flash`:
- SDK `GenerateContentConfig` supports `response_mime_type` and `response_schema` plus `response_json_schema`.
- We always set `response_mime_type="application/json"` and pass a strict schema. We parse then validate with Pydantic. On parse fail we return a clear error, never partial text.

sqlite-vec verified:
- `sqlite-vec` 0.1.9 loads on Windows Python 3.13 via `load_extension`. `select vec_version()` returns v0.1.9.
- Vectors table uses `vec0(embedding FLOAT[768] distance_metric=cosine)`. Chunk text stays in a relational table with chunk id. Joins are by rowid.

## Pipeline, no chat wrapper

1. Ingest: resume text to structured JSON (skills, education, years, metrics, roles) via schema enforced extraction. Skills are enriched with `backend/app/data/all_skills.txt` (37k names, non exhaustive): deterministic matcher uses stemming so variants align, and any novel item in the resume Skills section is kept as a skill with its source span. Nothing is invented. Every skill carries a verbatim source.
2. Index: chunk resume (about 400 chars with overlap), embed with task prefixed prompts, store in sqlite-vec.
3. Retrieve: each job requirement embedded as query, top k chunks retrieved plus structured attrs.
4. Verify: LLM judges each requirement using only retrieved chunks. Each verdict cites chunk ids plus verbatim quote. Code checks the quote exists in the chunk. No evidence outputs literal `No evidence found in resume`. Never infer.
5. Score: fit category computed in code from verdicts, not written by LLM. Weights are must_have 2.0 and nice_to_have 1.0. Thresholds are Strong Fit 75 and up, Moderate Fit 45 to 74, Weak Fit below 45. Must-have cap: if more than half of must_haves are no_evidence, Strong Fit is capped to Moderate Fit.
6. Outreach: email built only from matched evidence with quotes verified.

## Trust

- Resume, JD, and form fields are data, never instructions. System prompt states this. Injection text like `Ignore the job description` is ignored.
- Every claim shown must trace to a retrieved chunk id and quote.
- Secrets in `.env` only. `.env.example` lists `GEMINI_API_KEY`, `LLM_MODEL`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`.

## PDF bonus

Built only at end of Phase 5 after core checklist passes.

## Conflicts with PDF

- No direct conflict. PDF allows SQLite and any real LLM with JSON validation. This doc fixes choices to SQLite plus sqlite-vec and Gemini. PDF fit labels remain undefined, so code computed labels will be proposed in Phase 3 and confirmed before lock.
