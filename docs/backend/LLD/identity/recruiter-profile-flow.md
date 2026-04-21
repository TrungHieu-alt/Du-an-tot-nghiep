# LLD: Recruiter Profile Flow

## Source Anchors
- `backend/routers/recruiter_router.py`
- `backend/services/recruiter_service.py`
- `backend/repositories/recruiter_repo.py`
- `backend/models/recruiterProfile.py`

## Data Contract
`RecruiterProfile` fields:
- `user_id` (identity key)
- `company_name`
- `recruiter_title`
- `company_logo`
- `about_company`
- `hiring_fields`
- timestamps

Collection: `recruiter_profiles`

## Create Profile
Endpoint:
- `POST /api/recruiter/profile/{user_id}`

Execution:
1. Router validates `RecruiterProfileRequest`.
2. Service checks existing profile by `user_id`.
3. Repository inserts new profile.

Failure:
- profile already exists -> HTTP 400

## Get Profile
Endpoint:
- `GET /api/recruiter/profile/{user_id}`

Execution:
- Service returns recruiter profile or 404.

## Update Profile
Endpoint:
- `PUT /api/recruiter/profile/{user_id}`

Execution:
1. Router maps request body fields.
2. Service forwards update to repository.
3. Repository applies `$set` and refetches by `user_id`.

Failure:
- missing profile -> HTTP 404

## Design Notes
- No list endpoint currently exists for recruiter profiles.
- No auth ownership checks on read/update endpoints.
- `user_id` is authoritative lookup key.

## Related LLD
- User identity baseline: `user-auth-and-role-flow.md`
- API inventory: `../api/backend-endpoint-schema-matrix.md`
- Mongo model contracts: `../data/mongodb-model-id-and-index-contracts.md`
