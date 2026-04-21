# LLD: Backend Endpoint Schema Matrix

## Source Anchors
- `backend/routers/*.py`
- `backend/schemas/*.py`

## Purpose
Single source for endpoint inventory and primary request/response schema mapping.

## Users (`/api/users`)
- `POST /register`
  - request: `UserRegisterRequest`
  - response: `UserResponse`
- `POST /login`
  - request: `UserLoginRequest`
  - response: `TokenResponse`
- `GET /{user_id}` -> `UserResponse`
- `DELETE /{user_id}` -> message payload
- `PUT /{user_id}/role`
  - request: raw `dict` with `role`
  - response: `UserResponse`

## Candidate (`/api/candidate`)
- `POST /profile/{user_id}` -> `CandidateProfileRequest` -> `CandidateProfileResponse`
- `GET /profile/{user_id}` -> `CandidateProfileResponse`
- `PUT /profile/{user_id}` -> `CandidateProfileRequest` -> `CandidateProfileResponse`
- `GET /profiles` -> `List[CandidateProfileResponse]`

## Recruiter (`/api/recruiter`)
- `POST /profile/{user_id}` -> `RecruiterProfileRequest` -> `RecruiterProfileResponse`
- `GET /profile/{user_id}` -> `RecruiterProfileResponse`
- `PUT /profile/{user_id}` -> `RecruiterProfileRequest` -> `RecruiterProfileResponse`

## CV (`/api/cv`)
- `POST /create/{user_id}` -> `CandidateResumeRequest` -> `CandidateResumeResponse`
- `POST /upload/{user_id}` -> multipart file/form -> `CandidateResumeResponse`
- `POST /upload-text/{user_id}` -> form -> `CandidateResumeResponse`
- `GET /{cv_id}` -> `CandidateResumeResponse`
- `GET /user/{user_id}` -> `List[CandidateResumeResponse]`
- `GET /main/user/{user_id}` -> `CandidateResumeResponse`
- `PUT /{cv_id}` -> `CandidateResumeRequest` -> `CandidateResumeResponse`
- `DELETE /{cv_id}` -> message payload
- `GET /match/{cv_id}/jobs` -> `List[Dict]`
- `GET /match/{cv_id}/jobs/{job_id}` -> `Dict`

## Jobs (`/api/jobs`)
- `POST /create/{recruiter_id}` -> `JobPostRequest` -> `JobPostResponse`
- `POST /upload/{recruiter_id}` -> multipart file/form -> `JobPostResponse`
- `POST /upload-text/{recruiter_id}` -> form -> `JobPostResponse`
- `GET /` -> `List[JobPostResponse]`
- `GET /{job_id}` -> `JobPostResponse`
- `GET /recruiter/{recruiter_id}` -> `List[JobPostResponse]`
- `PUT /{job_id}` -> `JobPostRequest` -> `JobPostResponse`
- `DELETE /{job_id}` -> message payload
- `GET /match/{job_id}/cvs` -> `List[Dict]`
- `GET /match/{job_id}/cvs/{cv_id}` -> `Dict`

## Matching (`/api/matching`)
- `POST /job/{job_id}/run`
  - request: inline `RunMatchingRequest`
  - response: `RunMatchingResponse`
- `POST /cv/{cv_id}/run`
  - request: inline `RunMatchingRequest`
  - response: `RunMatchingResponse`
- `GET /job/{job_id}/matches` -> `JobMatchesResponse`
- `GET /cv/{cv_id}/matches` -> `CVMatchesResponse`
- `DELETE /cv/{cv_id}/matches` -> success envelope
- `DELETE /job/{job_id}/matches` -> success envelope

## Applications (`/api/applications`)
- `POST /`
  - request: inline `CreateApplicationRequest`
  - response: success envelope
- `GET /job/{job_id}` -> success envelope (paginated data)
- `GET /candidate/{candidate_id}` -> success envelope (paginated data)
- `PATCH /{app_id}/status`
  - request: inline `UpdateApplicationStatusRequest`
  - response: success envelope
- `DELETE /{app_id}`
  - response target: success envelope
  - runtime drift: service method missing (see dedicated drift note)

## System (`/api`)
- `GET /health` -> health payload

## Related LLD
- Router behavior and error patterns: `../runtime/router-contract-and-error-patterns.md`
- Application delete drift: `../applications/application-delete-flow-drift-note.md`
