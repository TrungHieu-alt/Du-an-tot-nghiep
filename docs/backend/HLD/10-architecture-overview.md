# Production HLD: Architecture Overview

## Runtime Layers

- API layer: FastAPI routers, request validation, response schemas, and OpenAPI
  contracts for the production namespaces.
- Auth and authorization layer: email/password login, JWT sessions, role checks,
  ownership checks, disabled-user blocking, and pool visibility rules.
- Domain services: users/profiles, organizations, resumes, jobs, documents,
  parsing, matching, applications, invites, notifications, audit, and admin
  monitoring.
- Data access layer: PostgreSQL repositories for production entities and
  pgvector-backed embeddings.
- Worker layer: asynchronous document parsing and embedding jobs.
- External services: object storage for original files, LLM parser, embedding
  model, optional reranker, and email delivery.

## Target Component Map

```text
FastAPI app
  ├─ auth
  ├─ users/profiles
  ├─ organizations
  ├─ documents + parse jobs
  ├─ candidate resumes
  ├─ job posts
  ├─ matching + search
  ├─ applications
  ├─ recruiter invites
  ├─ notifications
  └─ admin monitoring

Workers
  └─ parse pipeline
       ├─ object storage read
       ├─ text extraction/preprocess
       ├─ skill normalization
       ├─ LLM structured extraction
       └─ embedding generation

PostgreSQL + pgvector
  ├─ production relational entities
  └─ resume/job embedding tables
```

## Component Responsibilities

| Component | Responsibility |
|---|---|
| Auth | Register/login, password hashing, JWT issuance, role and status checks |
| Profiles | Candidate and recruiter profile CRUD |
| Organizations | Employer profile for recruiter-owned jobs |
| Documents | Original CV/JD metadata and object storage linkage |
| Parse jobs | Async extraction, normalization, LLM parse, embedding lifecycle |
| Resumes | Candidate-owned matching entities and active/draft/archive visibility |
| Jobs | Recruiter-owned matching entities and draft/published/closed lifecycle |
| Matching/search | Two-way matching, keyword search, semantic search, reasoning |
| Applications | Candidate apply and recruiter status transitions |
| Invites | Recruiter invite, candidate accept/reject, application creation on accept |
| Notifications | In-app notification records and basic email attempts |
| Audit | Business event trail for important lifecycle actions |
| Admin | Read-only monitoring of users, content, parse jobs, audit, and operations |

## Architectural Boundaries

- PostgreSQL is the source of truth for production business entities.
- Object storage is the source of truth for original uploaded files.
- pgvector embeddings support retrieval and scoring, but structured fields and
  visibility flags control eligibility.
- Matching results are recommendations and are not application records.
- Legacy prototype docs can be reused as migration reference, but runtime code
  implements production API contracts rather than `/api/v2/prototype/*`.
