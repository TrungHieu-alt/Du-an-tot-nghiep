# Production HLD: Ingestion And Normalization

## Goal

Convert uploaded CV/JD files into reviewed, structured, normalized, embedded
records that can safely enter public search and matching.

## Core Flow

```text
upload file
  -> store original in object storage
  -> create uploaded_documents row
  -> create parse_jobs row: queued
  -> worker marks processing
  -> extract raw text
  -> preprocess text
  -> normalize skills
  -> LLM structured parse with constrained schema
  -> update resume/job fields
  -> generate embeddings
  -> mark succeeded or failed
```

## File Handling

- MVP must support PDF upload. DOCX support is allowed only if extraction is
  tested.
- The original file is never deleted because parsing failed.
- Database metadata must include owner, document type, object key or URL,
  filename, MIME type, size, linked entity, timestamps, and parse error details.
- Upload returns after file persistence and parse job creation; parsing runs
  asynchronously.

## Preprocessing

Minimum preprocessing before LLM parsing:

- remove null bytes and invalid control characters.
- normalize Unicode to NFC for Vietnamese text.
- collapse excessive spaces and repeated blank lines.
- preserve technical terms and certification names.
- do not translate the entire document.

## Skill Normalization

- Normalize aliases before hard-filter extraction and embedding.
- MVP alias dictionary should contain about 50-100 high-impact entries.
- Matching uses normalized skill labels.
- Raw extracted terms may be retained for debugging, but must not drive canonical
  matching.

## LLM Structured Parse

- Parser input is preprocessed text plus a constrained JSON schema and allowed
  enum labels.
- Parser must map Vietnamese, English, and mixed text directly into canonical
  schema fields.
- Parser must not invent unsupported enum values.
- Parser output feeds only draft/reviewable resume or job records until the user
  activates or publishes the record.

### Adapter Boundary (Slice 6)

Implementations live under `backend/src/jobconnect/integrations/llm/`:

- `base.py` defines the `LLMParser` Protocol (`parse_resume`, `parse_job`,
  `parser_version`) and the `ParserError` exception.
- `local.py` wraps the Slice 5 deterministic keyword parser; `parser_version =
  "local-v1"`. This is the default fallback; no external credentials needed.
- `openai.py` calls an OpenAI-compatible chat completions endpoint with
  `response_format=json_object`. The adapter validates every enum field against
  the canonical sets before returning; raw unsupported values never reach the
  database. `parser_version = "openai-{model}-v1"`.

Selection happens in `get_parser()` based on env:

| Var | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `local` | `local` or `openai`. Unknown values fall back to local. |
| `OPENAI_API_KEY` | _(unset)_ | Required when `LLM_PROVIDER=openai`. If missing, factory logs and falls back to local. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Embedded in `parser_version`. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | For compatible endpoints / proxies. |
| `OPENAI_TIMEOUT_SECONDS` | `30` | httpx request timeout. |

Failure handling:

- `ParserError` from the adapter → worker marks parse job `failed` with
  `error_code = llm_parse_failed` and preserves the original file.
- Per-field invalid enum from LLM output → silently defaulted (per
  REQUIREMENTS §5.4) and never persisted as a raw label.
- Skills returned by the LLM are passed through the Slice 5 alias dictionary
  so canonical labels stay consistent across local/LLM modes.

## Parse Status

`parse_jobs.status` lifecycle:

- `queued`: file is stored and waiting for worker processing.
- `processing`: worker is extracting, normalizing, parsing, or embedding.
- `succeeded`: structured data and embeddings are available.
- `failed`: original file remains available and the user sees an actionable
  error.

## Failure Rules

- A parse failure does not delete the file or business entity.
- Email failure does not roll back parse state.
- Failed parse jobs should create user-visible notification and business audit
  entries.

