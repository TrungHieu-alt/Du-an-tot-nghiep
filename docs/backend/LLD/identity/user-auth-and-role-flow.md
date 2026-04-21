# LLD: User Auth and Role Flow

## Source Anchors
- `backend/routers/user_router.py`
- `backend/services/user_service.py`
- `backend/repositories/user_repo.py`
- `backend/auth.py`
- `backend/models/user.py`

## Data Contract
`User` document fields:
- `user_id` (manual integer sequence)
- `email`
- `password_hash`
- `role` in `candidate | recruiter | None`
- timestamps

Collection name: `users`

## Register Flow
Endpoint:
- `POST /api/users/register`

Execution:
1. Router validates `UserRegisterRequest`.
2. Service checks existing email via repository.
3. Password hashed with passlib argon2 (`hash_password`).
4. Repository generates new `user_id` via max+1 query and inserts document.

Failure conditions:
- duplicate email -> HTTP 400

## Login Flow
Endpoint:
- `POST /api/users/login`

Execution:
1. Service reads user by email.
2. Service verifies password (`verify_password`).
3. Service issues access token with payload `{sub: user_id}`.

Token details:
- JWT algorithm: `HS256`
- Access token expiry: 60 minutes
- Refresh token helper exists but is not used by routes.

Failure conditions:
- invalid credentials -> HTTP 401

## Read User Flow
Endpoint:
- `GET /api/users/{user_id}`

Execution:
- Service fetches by `user_id`, returns 404 if missing.

## Delete User Flow
Endpoint:
- `DELETE /api/users/{user_id}`

Execution:
- Service calls repository delete.
- Returns 404 if user not found.

Cascades:
- No automatic cascade to candidate/recruiter/CV/job/application data is implemented here.

## Update Role Flow
Endpoint:
- `PUT /api/users/{user_id}/role`

Execution:
1. Router accepts raw `payload: dict` and extracts `role`.
2. Service validates role membership in allowed values.
3. Repository loads user, mutates role, saves document.

Failure conditions:
- invalid role -> HTTP 400
- user missing -> HTTP 404

## Security Notes
- `SECRET_KEY` is hardcoded in `auth.py`.
- No route dependency currently checks bearer token.
- Auth utilities are present, authorization enforcement is limited.

## Related LLD
- Runtime conventions: `../runtime/router-contract-and-error-patterns.md`
- Candidate/recruiter profile flows: `candidate-profile-flow.md`, `recruiter-profile-flow.md`
