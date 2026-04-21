# Backend LLD Index

## Purpose
This folder contains low-level backend design aligned to current source code under `backend/` and linked from HLD.

## Scope
Included workflows:
- App bootstrap and API router surface
- Identity and profile flows
- CV and Job CRUD/upload/matching entrypoints
- RAG preprocessing, parsing, embedding, vector-store contracts
- Matching algorithm and persistence orchestration
- Application submission lifecycle
- Mongo/Chroma ownership boundaries and consistency risks

## LLD Authoring Rules
- One primary logic owner per file.
- No duplicated algorithm/process details across files.
- Cross-file references are allowed; repeated logic is not.
- Target length: 140-220 lines; hard ceiling: 250 lines.
- Strict loading rule: do not load any LLD file unless the active task requires low-level implementation detail that HLD does not provide.

## Folder Map
- `runtime/`: app startup and router-level contracts
- `identity/`: users, candidate profile, recruiter profile
- `cv/`: CV CRUD and CV ingestion internals
- `jobs/`: Job CRUD and Job ingestion internals
- `rag/`: preprocess/parser/embed/vector metadata contracts
- `matching/`: algorithm stages, service orchestration, query enrichment
- `applications/`: apply/query/status/delete behavior
- `data/`: Beanie model contracts, IDs, indexes, cross-store consistency
- `api/`: endpoint/schema matrix (single API inventory source)

## Primary Ownership Matrix
| Logic Area | Owner LLD File |
| --- | --- |
| FastAPI lifespan + mounted routers + CORS | `runtime/app-bootstrap-and-router-map.md` |
| Router request/response/error behavior conventions | `runtime/router-contract-and-error-patterns.md` |
| Register/login/role update/token behavior | `identity/user-auth-and-role-flow.md` |
| Candidate profile lifecycle | `identity/candidate-profile-flow.md` |
| Recruiter profile lifecycle | `identity/recruiter-profile-flow.md` |
| CV manual CRUD + main CV read logic | `cv/cv-manual-crud-and-main-cv-flow.md` |
| CV upload pipeline (file/text -> parse -> embed -> store) | `cv/cv-upload-parse-embed-store-flow.md` |
| Job manual CRUD | `jobs/job-manual-crud-flow.md` |
| Job upload pipeline (file/text -> parse -> embed -> store) | `jobs/job-upload-parse-embed-store-flow.md` |
| Resume preprocess + parse contract | `rag/resume-preprocess-and-parse-details.md` |
| JD preprocess + parse contract | `rag/job-preprocess-and-parse-details.md` |
| Embedding schema + Chroma metadata serialization | `rag/embedding-and-chromadb-metadata-contract.md` |
| Matching algorithm stages and formulas | `matching/matching-core-algorithm-details.md` |
| Run-matching orchestration + TOP-K sync persistence | `matching/matching-orchestration-and-topk-sync.md` |
| Match query enrichment + delete/cleanup semantics | `matching/match-query-enrichment-and-cleanup-flows.md` |
| Application create/query/status flow | `applications/application-create-query-status-flow.md` |
| Application delete drift note | `applications/application-delete-flow-drift-note.md` |
| Mongo model IDs and index contracts | `data/mongodb-model-id-and-index-contracts.md` |
| Cross-store non-transactional consistency behavior | `data/cross-store-consistency-and-failure-modes.md` |
| Endpoint + schema matrix | `api/backend-endpoint-schema-matrix.md` |

## Known Drift Registry
- Application delete endpoint exists in router, but `ApplicationService.delete_application` is missing.
  - Owner: `applications/application-delete-flow-drift-note.md`
- `application_router` uses inline request models instead of `schemas/application_schema.py`.
  - Owner: `runtime/router-contract-and-error-patterns.md`
- Chroma `skills` stored as JSON string but read paths often treat it as list-like data.
  - Owner: `rag/embedding-and-chromadb-metadata-contract.md`

## Reading Guide
Use HLD first. Load LLD files only for impacted workflows using the new `Related LLD` links inside HLD documents.
