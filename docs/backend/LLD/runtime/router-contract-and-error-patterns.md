# LLD: Router Contract and Error Patterns

## Source Anchors
- `backend/routers/*.py`
- `backend/schemas/*.py`

## Router Responsibilities
Routers currently own:
- Path/query/form body binding
- Pydantic request/response binding (partially consistent)
- Exception translation to HTTP responses

Routers do not own:
- Database logic
- Matching algorithm internals

## Request Contract Patterns
Observed patterns:
1. Strong typed request models from `schemas/*_schema.py`.
2. Inline request models declared in router files.
3. Multipart (`UploadFile` + `Form`) for CV/JD upload.

Most consistent typed routers:
- user, candidate, recruiter, cv, jobs, matching

Inline-model routers:
- application router defines `CreateApplicationRequest`, `UpdateApplicationStatusRequest` internally.

## Response Patterns
1. Direct model return with `response_model`:
   - used heavily in users/candidate/recruiter/cv/jobs/matching reads.
2. Envelope response with `success`, `data`, `message`:
   - used in `application_router`.

Implication:
- API response shape is inconsistent across domains.

## Error Handling Patterns
- `user/candidate/recruiter/cv/jobs`: business errors mostly raised in service via `HTTPException`.
- `matching`: catches generic exception in router, returns HTTP 500 with `detail=str(e)`.
- `applications`: converts `ValueError` -> HTTP 400, generic exception -> HTTP 500.

No shared exception mapping utility exists.

## Validation Boundaries
- Query constraints often applied via `Query`:
  - `top_k`, `limit`, `skip`, `min_score`.
- Application status validation is in service (not router).
- Role validation is in `UserService.update_role`.

## Router-Level Drift Notes
1. `application_router` calls `ApplicationService.delete_application(app_id)` but this method is not implemented.
2. `schemas/application_schema.py` exists, but `application_router` uses its own inline request classes instead.
3. Some delete endpoint docstrings in matching router mention re-run behavior while service notes they are cascade-delete only.

## Documentation Rule for API Inventory
To avoid duplication, endpoint-level route and schema inventory is centralized in:
- `api/backend-endpoint-schema-matrix.md`

This file should only define cross-router behavior patterns and drift.

## Related LLD
- App bootstrap and mounted prefixes: `runtime/app-bootstrap-and-router-map.md`
- API endpoint inventory: `api/backend-endpoint-schema-matrix.md`
- Application drift deep detail: `applications/application-delete-flow-drift-note.md`
