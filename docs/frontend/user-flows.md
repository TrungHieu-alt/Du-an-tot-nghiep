# User Flows

Archived experimental user-flow notes. These flows are not source of truth for
the next frontend implementation; future screens must be redesigned from
`docs/REQUIREMENTS.md`, backend HLD/LLD docs, and OpenAPI.

## Core Principles

- Separate user flow from core matching pipeline flow.
- Keep `exact search` and `semantic search` as different intents.
- Make extraction review mandatory before a record becomes canonical.
- Let users reach `run matching` from both upload-first and search-first paths.

## 1. Recruiter Primary Flow

Status: `Core MVP`

```text
Workspace Home
  -> Upload Job or Jobs Library
  -> Upload Wizard
  -> Extraction Review
  -> Save Result
  -> Job Detail
  -> Run Matching
  -> Matching Workspace / Results
  -> Open CV Detail or Compare
  -> Save shortlist
```

User goal:

- get from new JD to a reviewed shortlist quickly

Critical UX rules:

- preserve uploaded job as the selected anchor
- allow correction before save
- keep results actions visible without leaving context

## 2. Candidate Primary Flow

Status: `Core MVP`

```text
Workspace Home
  -> Upload CV or CVs Library
  -> Upload Wizard
  -> Extraction Review
  -> Save Result
  -> CV Detail
  -> Run Matching
  -> Matching Workspace / Results
  -> Open Job Detail or Compare
  -> Save jobs
```

User goal:

- move from uploaded CV to high-fit jobs with minimal friction

## 3. Search-First Flow

Status: `Core MVP`

```text
Workspace Home
  -> Jobs Library or CVs Library
  -> choose Exact Search or Semantic Search
  -> review results
  -> open detail
  -> run matching
```

Use when:

- the record already exists
- the user is exploring before uploading anything new

## 4. Prototype-Compatible Flow

Status: `Archived prototype reference`

```text
Search/Browse existing data
  -> Detail
  -> Matching Workspace
  -> Results
```

Why it matters:

- this flow described the removed prototype-adjacent UI direction
- it may be useful only as historical reference during a future redesign

## 5. Exact Search vs Semantic Search

Status: `Core MVP`

Exact search is for:

- title
- candidate name
- email
- exact structured field lookup

Semantic search is for:

- job description intent
- CV capability intent
- broader skill/experience meaning matches

Rules:

- do not merge them into one overloaded input
- visually explain why semantic results are ranked
- keep exact search fast and predictable

## 6. Save and Continuity Flows

Status: `Late MVP`

Saved entities should remain distinct:

- saved items
- shortlists
- recent runs
- recent searches

Reason:

- they support different user intents and different data models

## 7. Compare Flow

Status: `Late MVP`

```text
Results
  -> select 2-3 candidates or jobs
  -> Compare View
  -> review overlap and gaps
  -> shortlist / save / return
```

Use compare after the user already has a narrowed set. It should not be the first review surface.

## 8. Error Recovery Flows

Status: `Core MVP`

Must support:

- extraction fails
- upload invalid or unreadable
- no matches above threshold
- record missing
- session expires mid-flow

Recovery patterns:

- retry with minimal lost work
- preserve user input where possible
- provide one strong next action, not a wall of options

## 9. Role/Mode Switching

Status: `Core MVP`, but keep simple

The MVP should treat recruiter/candidate as workspace modes first unless product policy explicitly requires deeper permission separation.

Rule:

- switching mode must not disorient the user
- nav, home actions, and default library should adapt clearly

## 10. Future Extensions

Status: `Stretch`

Possible later flows:

- collaboration and sharing
- comments and review threads
- search replay and saved search alerts
- analytics dashboards
- external integrations

These should not distort the simpler MVP IA.
