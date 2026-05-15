# REQUIREMENTS.md — Production MVP Recruiting Marketplace

## 1. Product Goal

Build a production MVP recruiting marketplace with ATS-lite workflow and
explainable JD <-> CV matching.

The system serves three user groups:

- `candidate`: creates an account, uploads one or many CVs, chooses which CVs
  are active in the shared talent pool, searches/matches public jobs, applies to
  jobs, and responds to recruiter invites.
- `recruiter`: creates an account under an employer organization, uploads or
  creates job descriptions, publishes jobs to the shared pool, searches/matches
  active CVs, invites candidates, and manages applications.
- `admin`: monitors users, content, parse jobs, matching activity, notifications,
  and audit events. MVP admin is read-only unless a later requirement explicitly
  adds moderation write actions.

The MVP is a shared-pool marketplace, not a tenant-isolated SaaS product. All
published jobs and all active candidate resumes are visible to eligible matching
and search flows. There is no private company workspace isolation in MVP.

Large recruiting systems such as Greenhouse, Lever, and Workday frame recruiting
around candidate experience, pipeline management, automation/scheduling,
analytics, and AI-assisted recruiting. This MVP targets the core subset needed
for a credible production product: marketplace discovery, structured profiles,
two-way matching, application lifecycle, basic notifications, and auditability.

Reference benchmarks:

- Greenhouse platform: https://www.greenhouse.com/platform
- LeverTRM ATS + CRM: https://www.lever.co/lever-trm
- Workday Talent Acquisition: https://www.workday.com/en-us/products/talent-management/talent-acquisition.html

## 2. MVP Scope

### 2.1 In Scope

- Email/password authentication with JWT sessions.
- Roles: `candidate`, `recruiter`, `admin`.
- Candidate profile and recruiter profile management.
- Employer organization profile for recruiter-owned jobs.
- CV/JD file upload to object storage.
- Text extraction, preprocessing, skill normalization, LLM structured parsing,
  embedding generation, and parse status tracking.
- Candidate resume CRUD and activation into the public pool.
- Job post CRUD and publishing into the public pool.
- Keyword search by identity/title fields.
- Semantic search by JD/CV description fields.
- Two-way matching:
  - job -> active candidate resumes.
  - resume -> published jobs.
- Explainable ranking with score breakdown and deterministic tie-breaks.
- Candidate apply flow.
- Recruiter invite flow; accepted invite creates an application.
- ATS-lite application lifecycle: `submitted`, `shortlisted`, `rejected`,
  `hired`, `withdrawn`.
- In-app notifications plus basic email notifications.
- Business audit log for important lifecycle actions.
- OpenAPI-documented production API namespaces.

### 2.2 Out of Scope For MVP

- Company/tenant isolation or private workspaces.
- Billing, subscriptions, or quota enforcement.
- Full ATS interview scheduling, offer approvals, onboarding, or calendar sync.
- CRM/nurture campaigns.
- Destructive admin moderation UI, unless separately added.
- Salary, years of experience, languages, industry, visa/work authorization, and
  notice period as matching hard filters or score inputs.
- Fully configurable application stages.
- Knowledge graph for job titles/skills.
- BM25 hybrid retrieval.
- Automated reject/advance decisions made solely by AI.
- Production quality benchmarking conclusions without labeled evaluation data.

## 3. Canonical Enums And Statuses

The implementation must validate these values at API and persistence boundaries.

- `users.role`: `candidate | recruiter | admin`
- `users.status`: `active | invited | disabled`
- `candidate_resumes.status`: `draft | active | archived`
- `job_posts.status`: `draft | published | closed`
- `applications.status`: `submitted | shortlisted | rejected | hired | withdrawn`
- `recruiter_invites.status`: `pending | accepted | rejected`
- `parse_jobs.status`: `queued | processing | succeeded | failed`
- `notifications.status`: `unread | read`
- `location`: `ha_noi | tp_hcm | da_nang`
- `job_type`: `remote | fulltime | parttime`
- `seniority`: `intern | fresher | junior | mid | senior | lead`
- `education`: `lop_9 | lop_12 | dai_hoc | thac_si | tien_si`

Visibility rules:

- A resume enters the public candidate pool only when
  `candidate_resumes.status = active`.
- A job enters the public job pool only when `job_posts.status = published`.
- `draft`, `archived`, and `closed` records are excluded from public search and
  matching.

## 4. End-To-End User Flows

### 4.1 Candidate Onboarding And CV Activation

1. Candidate registers with email/password.
2. Candidate creates or updates a candidate profile.
3. Candidate uploads one or many CV files.
4. System stores the original file in object storage and creates a parse job.
5. System extracts text, preprocesses text, normalizes skills, parses structured
   fields, stores normalized resume data, and generates embeddings.
6. Candidate reviews the parsed resume.
7. Candidate sets one or more resumes to `active` to push them into the public
   pool.
8. Candidate can run matching from an active resume to find published jobs.
9. Candidate can apply to a published job with one chosen resume.

### 4.2 Recruiter Onboarding And Job Publishing

1. Recruiter registers with email/password.
2. Recruiter creates or joins an employer organization profile.
3. Recruiter creates a job post manually or uploads a JD file.
4. System stores the original JD file in object storage and creates a parse job.
5. System extracts text, preprocesses text, normalizes skills, parses structured
   fields, stores normalized job data, and generates embeddings.
6. Recruiter reviews the parsed job post.
7. Recruiter publishes the job to push it into the public marketplace pool.
8. Recruiter can run matching from a published job to find active candidate
   resumes.
9. Recruiter can invite a candidate resume to apply for the job.

### 4.3 Application And Invite Flow

- Matching results are recommendations only. Running matching must not create an
  application.
- Candidate application creates an `applications` record with status
  `submitted`.
- Recruiter invite creates a `recruiter_invites` record with status `pending`.
- If the candidate accepts an invite, the system creates an `applications`
  record with status `submitted` unless a duplicate application already exists.
- If the candidate rejects an invite, no application is created.
- Recruiter can move applications from `submitted` to `shortlisted`, `rejected`,
  or `hired`.
- Candidate can move their own application to `withdrawn` if it has not already
  reached a terminal recruiter decision.
- Every application status change creates an `application_events` row.

### 4.4 Notifications

The system creates in-app notifications and sends basic email for:

- candidate application submitted.
- recruiter invite sent.
- invite accepted or rejected.
- application status changed.
- parse job failed and requires user review.

Email delivery failure must not roll back the business transaction. The failure
must be logged for retry or operational review.

## 5. Ingestion And Parsing Coreflow

The production coreflow is:

```text
file upload
  -> object storage write
  -> text extraction
  -> text preprocessing
  -> Unicode NFC normalization
  -> skill normalization
  -> LLM structured extraction
  -> normalized DB fields
  -> embedding generation
  -> public search/matching eligibility
```

### 5.1 File Storage

- Original CV/JD files are stored in object storage such as AWS S3 or an
  S3-compatible service.
- The database stores object key or URL, owner user ID, document type, MIME type,
  file size, linked entity, parse status, timestamps, and error message if any.
- Supported MVP file types should include PDF. DOCX can be supported if the
  extractor is available and tested.
- The original file remains the source artifact for review, but matching uses
  normalized structured fields and embeddings.

### 5.2 Text Preprocessing

Preprocessing must run after raw text extraction and before structured parsing.
Minimum required behavior:

- Remove null bytes and invalid control characters.
- Normalize Unicode to NFC, especially for Vietnamese text.
- Collapse excessive whitespace and repeated blank lines.
- Preserve technical terms, programming languages, framework names, product
  names, and certification names.
- Do not translate the full document before extraction.

CV/JD text may be Vietnamese, English, or mixed. The parser must map directly
from mixed-language text into canonical labels.

### 5.3 Skill Normalization

- Normalize obvious aliases before hard-filter extraction and embedding.
- MVP alias dictionary should contain about 50-100 high-impact entries.
- Example mappings:

```text
reactjs, react.js, React -> react
pytorch, PyTorch -> pytorch
nodejs, node.js -> nodejs
```

- The system must store normalized skills in `skills` arrays.
- Raw extracted skills may be retained for debugging, but matching uses
  normalized skills.

### 5.4 LLM Structured Extraction

Use an LLM parser to map raw mixed-language CV/JD text into the canonical schema.

The parser must:

- Receive a JSON schema and the allowed enum labels in the prompt or constrained
  output configuration.
- Produce structured fields without inventing unsupported enum values.
- Map education, seniority, location, job type, skills, and certifications into
  canonical labels.
- Avoid full-document translation.
- Mark parse failures explicitly and preserve the original uploaded file for
  user review.

Example mappings:

```text
Master of Science in CS -> education: thac_si
Senior Developer -> seniority: senior
AWS SAA -> AWS Certified Solutions Architect Associate
Spring in a Java CV -> spring framework, not the season
```

## 6. Data Model Requirements

This section defines required entities and invariants. It is not a migration
file, but implementation tables must preserve these semantics.

### 6.1 Users And Profiles

`users`:

- `user_id BIGINT` primary key.
- `email` unique and required.
- `password_hash` required.
- `role` required: `candidate`, `recruiter`, or `admin`.
- `status` required: `active`, `invited`, or `disabled`.
- `created_at`, `updated_at`.

`organizations`:

- employer profile for recruiter-owned jobs.
- Required fields: ID, name.
- Optional display fields: slug, logo URL, about.

`recruiter_profiles`:

- one profile per recruiter user.
- links recruiter user to an organization.
- includes full name, title, and optional phone.

`candidate_profiles`:

- one profile per candidate user.
- includes full name, optional phone, current location, headline, and display
  metadata.
- `total_experience_years` is profile/display metadata only in MVP and is not a
  matching hard filter or score input.

### 6.2 Candidate Resumes

`candidate_resumes` is the matching entity for the CV side.

Required fields:

- `resume_id BIGINT` primary key.
- `candidate_user_id` owner.
- `title TEXT NOT NULL`.
- `summary TEXT NOT NULL DEFAULT ''`.
- `experience TEXT NOT NULL DEFAULT ''`.
- `skills TEXT[] NOT NULL DEFAULT '{}'`.
- `location`.
- `job_type`.
- `seniority`.
- `education`.
- `certifications TEXT[] NOT NULL DEFAULT '{}'`.
- `is_primary BOOLEAN NOT NULL DEFAULT false`.
- `status`: `draft`, `active`, or `archived`.
- timestamps.

Rules:

- A candidate may have multiple active resumes.
- `is_primary` is a display/default-selection hint only; it does not control
  pool visibility.
- Only active resumes are searchable and matchable by recruiters.

### 6.3 Job Posts

`job_posts` is the matching entity for the JD side.

Required fields:

- `job_id BIGINT` primary key.
- `organization_id`.
- `recruiter_user_id`.
- `title TEXT NOT NULL`.
- `requirement TEXT NOT NULL DEFAULT ''`.
- `skills TEXT[] NOT NULL DEFAULT '{}'`.
- `location`.
- `job_type`.
- `seniority`.
- `education`.
- `required_certifications TEXT[] NOT NULL DEFAULT '{}'`.
- `status`: `draft`, `published`, or `closed`.
- `published_at`, `expires_at`.
- timestamps.

Rules:

- Only published jobs are searchable and matchable by candidates.
- `published_at` must be set when status first becomes `published`.
- Closed jobs must not accept new applications or invites.

### 6.4 Documents And Parse Jobs

`uploaded_documents` is required for original CV/JD file tracking.

Minimum fields:

- `document_id BIGINT` primary key.
- `owner_user_id`.
- `document_type`: `candidate_resume | job_post`.
- `object_key` or `file_url`.
- `original_filename`.
- `mime_type`.
- `file_size_bytes`.
- linked `resume_id` or `job_id` when available.
- `created_at`.

`parse_jobs` is required for asynchronous extraction and embedding.

Minimum fields:

- `parse_job_id BIGINT` primary key.
- `document_id`.
- target entity type and ID.
- `status`: `queued`, `processing`, `succeeded`, or `failed`.
- extracted text or extracted text storage reference.
- parser version.
- embedding version requested.
- error code and error message.
- `started_at`, `finished_at`, timestamps.

Rules:

- Upload request should return after file persistence and parse job creation.
- Parse failure must not delete the original file.
- Users must be able to see whether their CV/JD is still processing, succeeded,
  or failed.

### 6.5 Embeddings

`candidate_resume_embeddings`:

- primary key: `resume_id`.
- vectors: `emb_title`, `emb_skills`, `emb_summary`, `emb_experience`.
- `embedding_version`.
- `updated_at`.

`job_post_embeddings`:

- primary key: `job_id`.
- vectors: `emb_title`, `emb_skills`, `emb_requirement`.
- `embedding_version`.
- `updated_at`.

Rules:

- Embedding version is mandatory to support future re-embedding/backfill.
- Missing field embeddings should not fail an entire matching run; the relevant
  score component becomes `0` and reasoning must mention the missing embedding.
- Vector dimension is `384` for the initial production MVP unless a later
  model-selection requirement changes it.

### 6.6 Applications And Events

`applications`:

- `application_id BIGINT` primary key.
- `job_id`.
- `candidate_user_id`.
- `resume_id`.
- `status`: `submitted`, `shortlisted`, `rejected`, `hired`, or `withdrawn`.
- `applied_at`, `updated_at`.

Rules:

- `(job_id, resume_id)` must be unique.
- Application status changes must be validated.
- Candidate can withdraw their own non-terminal application.
- Recruiter can shortlist, reject, or hire applications for their jobs.

`application_events`:

- append-only status history.
- includes application ID, from status, to status, actor user, note, and
  timestamp.

### 6.7 Recruiter Invites

`recruiter_invites` is required.

Minimum fields:

- `invite_id BIGINT` primary key.
- `job_id`.
- `resume_id`.
- `candidate_user_id`.
- `recruiter_user_id`.
- `status`: `pending`, `accepted`, or `rejected`.
- optional message.
- timestamps.

Rules:

- A pending invite does not create an application.
- Accepted invite creates an application if no `(job_id, resume_id)` application
  exists.
- Rejected invite creates no application.

### 6.8 Notifications

`notifications` is required.

Minimum fields:

- `notification_id BIGINT` primary key.
- `recipient_user_id`.
- `type`.
- `status`: `unread` or `read`.
- `title`.
- `body`.
- optional entity type and entity ID.
- optional email delivery status.
- timestamps.

### 6.9 Audit Logs

`audit_logs` is required for business events.

Minimum events:

- login/auth security events where useful.
- resume activated/archived.
- job published/closed.
- parse job failed.
- candidate applied.
- recruiter invite sent.
- invite accepted/rejected.
- application status changed.
- admin read/monitoring access where useful.

Audit logs must include actor user ID when known, event type, target entity,
timestamp, and metadata JSON.

## 7. Matching Requirements

### 7.1 Matching Modes

The production matching API must support:

- Job anchor: input `job_id`, rank active candidate resumes.
- Resume anchor: input `resume_id`, rank published jobs.

The anchor must be visible/eligible:

- Job anchor must be `published`.
- Resume anchor must be `active`.

### 7.2 Hard Filters

Hard filters apply both directions over shared JD/CV fields.

- `job_type` accepts `remote | fulltime | parttime`.
- If JD `job_type = remote`, skip hard filter `location`.
- If JD `job_type != remote`, `job_type` and `location` must match exactly.
- `seniority` must match exactly.
- `education` uses ordered taxonomy:

```text
lop_9 < lop_12 < dai_hoc < thac_si < tien_si
```

- CV education must be greater than or equal to JD required education.
- JD `required_certifications` must be fully contained in CV `certifications`.
- If required hard-filter data is missing on either side, the pair fails hard
  filter.

### 7.3 Score Formula

Initial production MVP keeps the prototype score formula:

```text
final_score =
  0.35 * title_sim +
  0.35 * skills_sim +
  0.20 * req_exp_sim +
  0.10 * req_summary_sim +
  bonus_exact_skill - penalty_missing_required
```

```text
skills_sim = 0.6 * semantic_skills + 0.4 * exact_overlap_ratio
```

MVP defaults:

- `top_k`: default `10`, allowed `1..50`.
- `min_score`: default `0.7`, allowed `0..1`.
- `bonus_exact_skill`: `0` until a measured rule is introduced.
- `penalty_missing_required`: `0` for pairs that already pass hard filters.

### 7.4 Retrieval And Reranking

- Embedding retrieval should produce a candidate set before final scoring.
- Cross-encoder reranking may be applied to the top 10-20 retrieved candidates
  when available.
- If cross-encoder reranking is unavailable, deterministic formula scoring must
  remain valid and explainable.
- Matching must be deterministic for the same data, model versions, and request
  parameters.

Tie-break:

- Sort by `final_score DESC`.
- For job -> resume matching, then `resume_id ASC`.
- For resume -> job matching, then `job_id ASC`.

### 7.5 Reasoning

Reasoning must be explainable and safe for users.

Minimum reasoning content:

- strongest matching components.
- exact skill overlap count.
- seniority/location/education/certification pass notes.
- missing embedding notes if any component score was forced to `0`.

LLM-generated reasoning is allowed only if it is grounded in the structured score
breakdown and must not invent facts absent from the CV/JD data.

## 8. Search Requirements

The UI and API must separate keyword search from semantic search.

### 8.1 Keyword Search

Use keyword/full-text search for identity/title fields:

- candidate name.
- candidate email, subject to role/privacy permissions.
- recruiter or organization name.
- resume title.
- job title.

Keyword search is not the same as semantic JD/CV matching.

### 8.2 Semantic Search

Use embedding search for meaning-based queries:

- search jobs by candidate intent or CV-style description.
- search resumes by job requirement text.
- support filters for `location`, `job_type`, and `seniority`.

Semantic search scores are retrieval relevance scores and are not the final
matching score from Section 7.

## 9. API And OpenAPI Requirements

The production API is a breaking replacement for prototype-only routes under
`/api/v2/prototype/*`.

Production namespaces must be defined and documented in OpenAPI:

- `/api/auth/*`
- `/api/me`
- `/api/candidate/profile`
- `/api/candidate/resumes/*`
- `/api/recruiter/profile`
- `/api/organizations/*`
- `/api/jobs/*`
- `/api/documents/*`
- `/api/matching/*`
- `/api/applications/*`
- `/api/invites/*`
- `/api/notifications/*`
- `/api/admin/*`

Required contract rules:

- All request/response bodies must have explicit schemas.
- All enums must be represented in OpenAPI.
- File upload endpoints must document accepted MIME types and max size.
- Parse status endpoints must expose `queued`, `processing`, `succeeded`, and
  `failed`.
- Matching responses must include score breakdown and reasoning.
- Application/invite mutation endpoints must document allowed status
  transitions.
- API changes must be classified as breaking or non-breaking in implementation
  handoff notes.

## 10. Security And Privacy

- Authentication uses email/password plus JWT.
- Passwords must be stored only as secure hashes.
- Candidate users can manage only their own profile, documents, resumes,
  applications, invites, and notifications.
- Recruiters can manage only their own job posts and organization-linked
  recruiting actions.
- Recruiters can search/match only active resumes in the public pool.
- Candidates can search/match only published jobs in the public pool.
- Candidate contact data must not be exposed beyond what the role and flow
  require.
- Disabled users cannot publish, activate, apply, invite, or run matching.
- The MVP has no tenant isolation; do not add hidden company-private behavior
  unless requirements are changed.

## 11. Observability And Audit

Minimum operational visibility:

- parse queue status and failure reasons.
- matching request count and latency.
- notification creation and email delivery failure.
- application and invite lifecycle events.
- API error rates for auth, upload, parse, matching, and application flows.

Minimum audit events are listed in Section 6.9.

Audit and operational logs must not store raw passwords, JWTs, or sensitive file
contents.

## 12. Validation And Acceptance Criteria

### 12.1 Account And Profile

- [ ] Candidate, recruiter, and admin users can authenticate with JWT.
- [ ] Candidate can create/update candidate profile.
- [ ] Recruiter can create/update recruiter profile and organization profile.
- [ ] Disabled users cannot perform marketplace actions.

### 12.2 Document Ingestion

- [ ] Candidate can upload a CV file and receive parse status.
- [ ] Recruiter can upload a JD file and receive parse status.
- [ ] Parse job transitions through `queued`, `processing`, and either
      `succeeded` or `failed`.
- [ ] Text preprocessing performs Unicode NFC normalization.
- [ ] LLM parser maps mixed Vietnamese/English input into canonical enums.
- [ ] Skill aliases are normalized before storage and matching.
- [ ] Failed parse keeps the original file and exposes an actionable error.

### 12.3 Pool Visibility

- [ ] `candidate_resumes.status = active` resumes appear in public resume search
      and matching.
- [ ] `draft` and `archived` resumes are excluded from public resume search and
      matching.
- [ ] `job_posts.status = published` jobs appear in public job search and
      matching.
- [ ] `draft` and `closed` jobs are excluded from public job search and matching.

### 12.4 Matching

- [ ] Job -> resume matching returns ranked active resumes.
- [ ] Resume -> job matching returns ranked published jobs.
- [ ] Response includes rank, final score, score breakdown, exact skill overlap,
      and reasoning.
- [ ] Remote jobs skip location hard filter.
- [ ] Non-remote jobs require exact location and job type match.
- [ ] Education taxonomy is enforced.
- [ ] Required certifications are enforced.
- [ ] Missing field embeddings set only that score component to `0` and are
      mentioned in reasoning.
- [ ] Same request over unchanged data returns deterministic order.

### 12.5 Search

- [ ] Keyword search handles name/email/title-style queries.
- [ ] Semantic search handles description-style queries.
- [ ] UI/API do not mix keyword and semantic search into one ambiguous search
      behavior.

### 12.6 Applications And Invites

- [ ] Candidate can apply to a published job using an active resume.
- [ ] Duplicate `(job_id, resume_id)` applications are rejected.
- [ ] Recruiter can invite an active resume to a published job.
- [ ] Pending invite does not create an application.
- [ ] Accepted invite creates an application.
- [ ] Rejected invite does not create an application.
- [ ] Recruiter can move application to `shortlisted`, `rejected`, or `hired`.
- [ ] Candidate can withdraw eligible application.
- [ ] Every status change creates an application event.

### 12.7 Notifications And Audit

- [ ] Apply, invite, invite response, status change, and parse failure create
      in-app notifications.
- [ ] Basic email is attempted for the same important events.
- [ ] Email failure is logged and does not roll back the business action.
- [ ] Business audit events are recorded for publish/unpublish, apply, invite,
      invite response, status change, and parse failure.

## 13. Test And Verification Policy

Implementation tasks derived from this requirement must include:

- OpenAPI contract verification for all changed endpoint families.
- Auth and role-boundary tests for candidate, recruiter, and admin flows.
- Upload/parse success and parse failure tests.
- Visibility tests for active/draft/archived resumes and
  published/draft/closed jobs.
- Matching tests that preserve deterministic prototype cases for hard filters,
  score formula, tie-breaks, missing embeddings, and two-way matching.
- Application and invite lifecycle tests.
- Notification and audit creation tests for important lifecycle actions.

Until there is a labeled evaluation set, matching quality claims must be limited
to deterministic scenario evidence. Precision, recall, NDCG, and model
comparison benchmarks are later-phase work.

## 14. Current Implementation Compatibility Notes

The repository implementation now exposes production `/api/*` namespaces and
stores the schema migration under `backend/db/migrations/`.
Legacy `/api/v2/prototype/*` runtime code has been removed; legacy prototype
documents remain as reference material only.

Remaining implementation work should focus on provider-backed ingestion, real
object storage, LLM parsing, production embedding/rerank choices, email
delivery, broader automated coverage, and the next production frontend.
