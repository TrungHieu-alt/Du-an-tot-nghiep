# Design References And Style Rationale

Status: production-like MVP planning
Documentation language: English

## 1) Purpose

Record external product and layout references that informed the Slice 13 screen
direction, and state the explicit style decision to keep frontend implementation
scope realistic for MVP.

## 2) External Product References

The following products were referenced for layout, interaction, and information
density patterns. None are to be copied; they are directional input only.

| Reference | Aspect used |
|---|---|
| [Workable](https://workable.com) | Candidate pipeline list, application card density, status badge placement, filter sidebar |
| [Greenhouse](https://greenhouse.com) | Job detail layout, application event timeline, admin user list |
| [LinkedIn Jobs](https://linkedin.com/jobs) | Job card grid/list hybrid, semantic search bar with filter chips |
| [TopCV.vn](https://topcv.vn) | Vietnamese recruiting context, CV card format, candidate-facing job list |
| [Notion](https://notion.so) | Document-style detail pages, inline field editing, audit trail display |
| [Linear](https://linear.app) | Dense list views, status transitions, keyboard-first interactions |

References were used at layout and density level only. Visual tokens (color,
radius, shadow) are not sourced from these products.

## 3) Style Decision

The chosen style level is: **data-first, low-polish, operationally clear**.

Rationale:
- MVP priority is correct data display and workflow completion, not visual brand.
- Dense information display (two-column detail pages, list + side panel where
  relevant) beats decorative whitespace for daily operational usage.
- Vietnamese language UI requires consistent, non-truncating text handling;
  clean table-style layouts handle this better than card-heavy grids.
- Visual polish and brand color refinement is explicitly deferred to post-MVP.

Explicit non-goals for MVP style:
- Animated transitions.
- Custom illustration or icon sets.
- Dark mode.
- Brand-specific color palette beyond a neutral baseline.

## 4) Component Library Decision

For Slice 14 frontend shell implementation:

- **Primary**: [shadcn/ui](https://ui.shadcn.com/) — MIT licensed, Tailwind-based,
  accessible primitives, no runtime vendor lock-in.
- **Styling**: Tailwind CSS with the default slate/neutral palette as base;
  accent colors can be configured per brand direction later.
- **Icons**: [lucide-react](https://lucide.dev/) — consistent line icons, MIT,
  tree-shakable.

No Figma handoff is required for MVP; screen specs in `docs/frontend/screen/`
serve as the engineering design brief directly.

## 5) Frontend Assumptions For Slice 14

The following assumptions are recorded so Slice 14 does not need to re-derive
them from the backend surface:

| Assumption | Source |
|---|---|
| JWT is returned in `access_token` field at login/register | Slice 1 contract |
| Token type is Bearer; auth header: `Authorization: Bearer <token>` | Slice 1 contract |
| Role is in JWT payload: `candidate`, `recruiter`, `admin` | Slice 1 contract |
| `GET /api/me` returns `{user, candidate_profile, recruiter_profile, organization}` | Smoke test verified |
| Profile PUT endpoints return 200 even on first creation | Smoke test verified |
| All non-2xx errors use `{"error": {"code", "message"}}` envelope | Slice 12 verified |
| Validation errors are `422` with `{"error": {"code": "validation_error", "fields": {}}}` | Slice 12 verified |
| CORS allows `localhost:5173` and `localhost:3000` by default | Slice 12 verified |
| Resume activate/archive are dedicated POST endpoints: `POST .../activate`, `POST .../archive` | Smoke test verified |
| Job publish/close are dedicated POST endpoints: `POST .../publish`, `POST .../close` | Smoke test verified |
| Application status update: `POST /api/applications/{id}/status` | Smoke test verified |
| Invite accept/reject: `POST /api/invites/{id}/accept`, `POST /api/invites/{id}/reject` | Smoke test verified |

## 6) Blocked API Dependencies (Required Before Full Screen Implementation)

The following backend API changes are required before some screens can be fully
implemented. See `screen-to-api-state-matrix.md` and `upload-parse-review.md`
for detailed requirements.

| Blocked screen | Required API change | Priority |
|---|---|---|
| Upload + Parse Review | `parse_jobs` detail must expose normalized parsed fields + target entity ID | P0 — blocks entire upload flow UI |
| Job Market cards | `GET /api/jobs/search` must return `organization_name`, `organization_logo_url` | P1 — needed for card display |
| My Activity / Application list | List responses need denormalized `job_title`, `resume_title`, `applied_at` | P1 — needed for list display without N+1 fetches |
| Recruiter Application Management | Application list needs denormalized job/resume summaries | P1 |
| Recruiter onboarding | DB must have a seeded `Independent` org row for `Khác` option | P1 |

None of these block the Slice 14 shell (routing, auth, API client, nav). They
block full workflow screen implementation in Slice 15.
