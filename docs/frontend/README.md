# Frontend Documentation Hub

This folder contains two document groups:

- Archived experimental notes from earlier prototype-adjacent work.
- New screen-by-screen specs under `docs/frontend/screen/` for current planning.

## Scope

- Product shape: unified recruiter/candidate workspace centered on `Job Market`
  for candidate discovery/matching, `Talent Market` for recruiter
  discovery/matching, and shared detail screens for lifecycle work.
- Design scope: MVP-first, desktop-first, responsive down to tablet/mobile
- Execution intent: archived docs are reference-only; `screen/` docs are active
  planning artifacts.
- Language contract: documentation is written in English; visible UI labels,
  CTAs, validation messages, empty states, and blocked/error messages are
  specified in Vietnamese.

## Canonical Naming (Current Planning)

- `Workspace` in legacy wording maps to `Job Market` as the primary candidate
  home screen for discovery + in-screen matching.
- Recruiter-side discovery + in-screen matching maps to `Talent Market`.
- `CV adjustment` maps to `Resume Detail` as the primary self-management screen
  for editing and lifecycle actions.
- `Records Management` is a secondary operational library view, not the primary
  workspace entry.

## Current Baseline

The repository currently has no active frontend runtime. The V2 prototype
frontend has been removed from runtime code.

## Source of Truth

- Product and matching constraints: `docs/REQUIREMENTS.md`
- Backend runtime boundaries today: `docs/backend/HLD/50-api-and-runtime-flows.md`
- API contract details: `docs/backend/LLD/40-api-contract.md`

## Archived Documents

- `design-system.md`: visual tokens, component rules, and layout patterns
- `screen-specifications.md`: screen-by-screen UI contract for wireframe and implementation
- `user-flows.md`: key recruiter/candidate flows and failure recovery paths
- `figma-implementation-guide.md`: practical build guide for Figma handoff
- `ATTRIBUTIONS.md`: third-party asset and component attribution

## Active Screen Docs

- `screen/auth-screen.md`: login and sign-up screen specification
  (desktop/mobile, validation, states, and interaction rules).
- `screen/candidate-profile-setup.md`: candidate profile setup with optional CV upload,
  single-form now and multi-screen-ready structure.
- `screen/recruiter-profile-setup.md`: recruiter profile setup with organization search,
  `Khác` organization mapping, and logo display.
- `screen/upload-parse-review.md`: dedicated upload page for CV/JD with full
  parse preview, mandatory hard-filter confirmation, and embedding fields review.
- `screen/job-market.md`: candidate job discovery screen with exact/semantic
  modes, minimal filters, and company-logo-ready job cards.
- `screen/talent-market.md`: recruiter candidate discovery screen with
  exact/semantic modes, minimal filters, and invite/matching-ready resume cards.
- `screen/job-detail.md`: full job record detail screen, shared detail pattern
  with lifecycle and matching actions.
- `screen/resume-detail.md`: full resume record detail screen, shared detail
  pattern with lifecycle and matching actions.
- `screen/records-management.md`: unified operational list screen for jobs and
  CV records with exact/semantic modes and quick actions.
- `screen/invite-application-flow.md`: candidate activity flow for applied jobs
  and incoming invites, with route navigation to dedicated detail pages.
- `screen/account-settings.md`: minimal settings screen aligned to current
  backend APIs (profile update, notifications, logout).
- `screen/application-management.md`: recruiter-facing application pipeline
  management by job, status transitions, and event timeline entry points.
- `screen/admin-monitoring.md`: read-only admin monitoring dashboard and list
  screens for users, documents, parse jobs, applications, invites,
  notifications, and audit logs.
- `screen/shared-states.md`: shared Vietnamese empty, blocked, authorization,
  session-expired, validation, and fallback state contract.
- `screen-to-api-state-matrix.md`: implementation matrix mapping each screen to
  routes, roles, APIs, states, success navigation, and blocked actions.

## Notes for Engineers

- Treat archived docs as historical reference only.
- For new frontend screen planning, use files under `docs/frontend/screen/`.
- Backend/API contracts should be documented from the OpenAPI surface and
  backend HLD/LLD docs, not duplicated here.
