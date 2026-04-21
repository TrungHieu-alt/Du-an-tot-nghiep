# LLD: Application Delete Flow Drift Note

## Source Anchors
- `backend/routers/application_router.py`
- `backend/services/application_service.py`
- `backend/repositories/application_repo.py`

## Intended Delete Endpoint Contract
Route defined:
- `DELETE /api/applications/{app_id}`

Router implementation calls:
- `ApplicationService.delete_application(app_id)`

## Actual Source State
`ApplicationService` currently does not implement `delete_application`.

Impact:
- endpoint will fail at runtime when invoked.
- API surface advertises delete behavior that service layer cannot execute.

## Expected Implementation Shape (based on existing patterns)
If implemented consistently with current architecture:
1. Service method validates existence and/or delegates to repository delete.
2. Repository `delete(app_id)` performs document delete and returns boolean.
3. Service maps not-found to `ValueError` or `HTTPException` consistently.
4. Router returns success envelope.

## Risk Classification
- Severity: high for endpoint reliability.
- Scope: only application delete operation.
- Data safety: no destructive behavior currently triggered because path errors early.

## Documentation Policy for This Drift
- Keep this drift note until source code implements delete service method.
- Do not describe delete as operational in other LLD/HLD docs without caveat.

## Related LLD
- Main application lifecycle doc: `application-create-query-status-flow.md`
- API behavior patterns: `../runtime/router-contract-and-error-patterns.md`
