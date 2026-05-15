# Archived Figma Experiment Guide

This file is an archived prototype-adjacent experiment note. It is not source of
truth for the next frontend, and future screens should be redesigned from
`docs/REQUIREMENTS.md`, backend HLD/LLD docs, and the current OpenAPI surface
before implementation.

The notes below remain only as historical reference for possible interaction
patterns and handoff checklist items.

## 1. File Structure

Recommended page order:

```text
Cover
Design System
Components
Recruiter Flows
Candidate Flows
Shared States
Prototype Links
Developer Handoff
```

## 2. Start with Foundations

Create variable collections for:

- colors
- spacing
- typography
- radius
- shadows

Do this before drawing screens. The temp design pack was detailed enough, but the repo version should stay token-first so future implementation does not drift.

## 3. Build Shared Components First

Priority order:

1. buttons
2. text inputs
3. search inputs
4. segmented controls / tabs
5. badges and skill pills
6. result cards
7. sticky action rail
8. empty/error blocks

Do not start with full screens before these exist.

## 4. Screen Build Order

Recommended order for wireframe and hi-fi work:

1. Matching Workspace
2. Jobs Library
3. CVs Library
4. Job Detail
5. CV Detail
6. Upload Wizard
7. Auth Gateway
8. Workspace Home
9. Results Focus View
10. Compare View
11. Saved / History

Reason:

- the first five screens mapped most directly to the removed prototype baseline and MVP backbone

## 5. Match the Product Model

Keep these distinctions visible in Figma:

- recruiter mode vs candidate mode
- exact search vs semantic search
- uploaded draft vs saved record
- current result view vs saved shortlist

If these distinctions disappear in the design file, implementation confusion will follow.

## 6. Extraction Review Page Rules

This screen needs more than a generic review form.

Required zones:

- raw extracted text
- structured normalized fields
- validation and confidence warnings
- next-step action row

Use side-by-side comparison where possible on desktop.

## 7. Matching Workspace Rules

- preserve the 3-column structure
- make anchor changes obvious
- keep controls near the anchor preview
- keep results scan-friendly
- expose score and reasoning without forcing modal drills for every row

## 8. Responsive Guidance

Desktop:

- full three-column layouts allowed

Tablet:

- convert sidebars to drawers or stacked sections

Mobile:

- prioritize read, review, and light refinement tasks
- do not force complex compare workflows into cramped multi-column layouts

## 9. Handoff Checklist

Before calling the file ready for engineering:

- all tokens named consistently
- all repeated UI converted to components
- interactive states shown for primary actions
- empty/error/loading states included
- navigation and screen names are explicitly revalidated against current product docs
- one note on each screen states whether it is `Core MVP`, `Late MVP`, or `Stretch`

## 10. Developer Notes to Include in Figma

Add annotation blocks for:

- fields that come from exact search
- fields that come from semantic ranking
- upload pipeline dependencies
- actions that require backend persistence

This avoids the common handoff failure where visuals are clear but data semantics are not.
