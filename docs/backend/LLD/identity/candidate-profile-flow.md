# LLD: Candidate Profile Flow

## Source Anchors
- `backend/routers/candidate_router.py`
- `backend/services/candidate_service.py`
- `backend/repositories/candidate_repo.py`
- `backend/models/candidateProfile.py`

## Data Contract
`CandidateProfile` fields:
- `user_id` (identity key)
- `full_name`
- `location`
- `experience_years`
- `skills`
- `summary`
- timestamps

Collection: `candidate_profiles`

## Create Profile
Endpoint:
- `POST /api/candidate/profile/{user_id}`

Execution:
1. Router validates `CandidateProfileRequest`.
2. Service checks profile existence by `user_id`.
3. Repository inserts profile if not exists.

Failure:
- profile already exists -> HTTP 400

## Get Profile
Endpoint:
- `GET /api/candidate/profile/{user_id}`

Execution:
- Service reads profile by `user_id` and returns 404 if missing.

## Update Profile
Endpoint:
- `PUT /api/candidate/profile/{user_id}`

Execution:
1. Router maps request fields to kwargs.
2. Repository loads by `user_id`, applies `$set`, then refetches.

Failure:
- missing profile -> HTTP 404

## List Profiles
Endpoint:
- `GET /api/candidate/profiles`

Execution:
- Service returns all candidate profiles without paging.

## Design Notes
- `user_id` doubles as foreign key and profile lookup key.
- No uniqueness index is explicitly declared in model settings.
- No auth guard validates caller identity ownership.

## Related LLD
- User identity baseline: `user-auth-and-role-flow.md`
- API inventory: `../api/backend-endpoint-schema-matrix.md`
- Mongo model contracts: `../data/mongodb-model-id-and-index-contracts.md`
