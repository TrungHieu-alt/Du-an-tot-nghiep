# Screen Specifications

Archived experimental screen notes. This document is not source of truth for the
next frontend implementation. Future screens must be redesigned from product,
backend, and OpenAPI docs.

## Delivery Labels

- `Core MVP`: expected in the first complete MVP cut
- `Late MVP`: valuable for MVP polish, but can follow core flows
- `Stretch`: useful direction, not required to validate the product end-to-end

## 1. Auth Gateway

Label: `Core MVP`

Purpose:

- entry point for sign in / sign up
- lets user continue in recruiter or candidate mode

Requirements:

- simple, direct split between the two modes
- no deep RBAC configuration here
- must support empty-state onboarding copy

Primary actions:

- `Continue as Recruiter`
- `Continue as Candidate`
- `Sign in`
- `Create account`

## 2. Workspace Home

Label: `Core MVP`

Purpose:

- operational home, not a marketing landing page
- expose the most important next actions immediately

Recruiter quick actions:

- upload job
- search CVs
- run matching from job
- open jobs library

Candidate quick actions:

- upload CV
- search jobs
- run matching from CV
- open CV library

Secondary modules:

- recent items
- recent matching runs
- saved items summary

## 3. Jobs Library

Label: `Core MVP`

Purpose:

- browse and search job records

Required structure:

- page header with count and primary CTA
- tabs or segmented control:
  - `Exact search / browse`
  - `Semantic search`
- filter region
- result region

Exact mode:

- title-based and structured-field search
- traditional filters and sorting

Semantic mode:

- dedicated query field
- score-based results
- explicit semantic indicator

Primary actions:

- open detail
- run matching
- upload job

## 4. CVs Library

Label: `Core MVP`

Purpose:

- symmetric counterpart to jobs library

Differences from jobs:

- exact mode may include candidate name / email / title search
- result cards emphasize skills, summary, and experience fit

Primary actions:

- open detail
- run matching
- upload CV

## 5. Job Detail

Label: `Core MVP`

Purpose:

- full reading and decision page for a single job

Layout:

- main content column
- sticky right action rail

Must-have fields:

- title
- location
- job type
- seniority
- education
- required certifications
- skills
- requirement text
- source status if upload pipeline is implemented

Actions:

- run matching from this job
- edit metadata
- open original file when available

## 6. CV Detail

Label: `Core MVP`

Purpose:

- full reading and decision page for a single candidate profile

Must-have fields:

- title
- location
- preferred job type
- seniority
- education
- certifications
- skills
- summary
- experience
- source status if upload pipeline is implemented

Actions:

- run matching from this CV
- edit metadata
- open original file when available

## 7. Upload Wizard

Label: `Core MVP`

Purpose:

- structured ingestion flow for CVs and JDs

Step 1:

- choose type: CV or JD
- choose source: file upload or paste text

Step 2:

- extraction review
- raw text preview
- normalized field preview
- low-confidence or invalid extraction warnings

Step 3:

- save confirmation
- next-step CTAs

Actions after save:

- open detail
- run matching now
- back to library

## 8. Matching Workspace

Label: `Core MVP`

Purpose:

- stable, central matching screen

Layout:

- left: anchor picker
- center: anchor preview and controls
- right: ranked results

Baseline controls:

- `top_k`
- `min_score`

Allowed future extension:

- ranking profile
- rerank mode
- explainability depth

## 9. Matching Results Focus View

Label: `Late MVP`

Purpose:

- expanded results review for deeper triage

Must-have areas:

- stats banner
- filters and sorting
- detailed result cards
- score breakdown
- reasoning summary

Result actions:

- open detail
- compare
- save shortlist
- save run

## 10. Compare View

Label: `Late MVP`

Purpose:

- compare one job against one or more CVs, or one CV against one or more jobs

Comparison layers:

- exact metadata fit
- skills overlap
- requirement vs experience
- reasoning summary

Rules:

- start with 2-column comparison
- allow 3+ columns only if readability remains acceptable

## 11. Saved / History

Label: `Late MVP`

Purpose:

- preserve user continuity

Separate tabs:

- recent searches
- matching runs
- saved items
- shortlists

Do not blur these into one mixed list.

## 12. Empty / Error / Not Found States

Label: `Core MVP`

Required states:

- empty library
- no exact results
- no semantic results
- no matches above threshold
- extraction failed
- item not found
- network error
- session expired
- upload error

## Prototype Mapping Notes

The removed prototype codebase covered a smaller subset that can be used only as
historical reference:

- search/browse surface
- job detail
- CV detail
- matching workspace

Those prototype screens should be treated as historical examples, not as a
starting point for implementation or final IA boundary.
