# Archived Frontend Experiment Notes

This folder contains experimental, prototype-adjacent frontend notes.

These files are **not** source of truth for the next frontend implementation.
The team decided not to use them because they stay too close to the removed
frontend prototype. Future screens should be redesigned later from
`docs/REQUIREMENTS.md`, backend HLD/LLD docs, and the current OpenAPI surface.

## Scope

- Product shape: unified recruiter/candidate workspace
- Design scope: MVP-first, desktop-first, responsive down to tablet/mobile
- Execution intent: archived reference only, not implementation planning

## Current Baseline

The repository currently has no active frontend runtime. The V2 prototype
frontend has been removed from runtime code.

## Source of Truth

- Product and matching constraints: `docs/REQUIREMENTS.md`
- Backend runtime boundaries today: `docs/backend/HLD/50-api-and-runtime-flows.md`
- API contract details: `docs/backend/LLD/40-api-contract.md`

## Documents

- `design-system.md`: visual tokens, component rules, and layout patterns
- `screen-specifications.md`: screen-by-screen UI contract for wireframe and implementation
- `user-flows.md`: key recruiter/candidate flows and failure recovery paths
- `figma-implementation-guide.md`: practical build guide for Figma handoff
- `ATTRIBUTIONS.md`: third-party asset and component attribution

## Working Rules

- Keep `exact search` and `semantic search` as distinct flows in IA and UI.
- Keep `Matching Workspace` as the stable core screen even as MVP grows.
- Treat upload and extraction review as first-class product flows, not optional polish.
- Prefer one shared layout skeleton for `Job Detail` and `CV Detail`.
- Mark features as `Core MVP`, `Late MVP`, or `Stretch` when implementation order matters.

## Notes for Engineers

- Treat this folder as archived reference.
- Do not implement screens directly from these files without a new frontend
  redesign pass.
- Backend/API contracts should be documented from the OpenAPI surface and
  backend HLD/LLD docs, not duplicated here.
