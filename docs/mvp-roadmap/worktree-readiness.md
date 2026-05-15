# Worktree Readiness

The repository may contain unrelated or pre-existing dirty changes. Slice work
must not accidentally mix those changes with new implementation.

Use this checklist before starting a code slice.

## Start Checklist

Run:

```bash
git status --short
```

Then record in `docs/mvp-roadmap/progress.md`:

- branch name,
- whether the worktree is clean,
- unrelated dirty files already present,
- expected touched files for the slice.

## Dirty Worktree Rules

- Do not revert unrelated dirty files.
- Do not format or rewrite unrelated files.
- If the slice needs to edit a file that already has unrelated changes, inspect
  the file carefully and record the risk in the slice handoff.
- If same-file unrelated changes make the slice ambiguous, stop and ask for a
  checkpoint or owner decision before editing that file.
- Keep docs-only slice changes separate from code slice changes where practical.

## Recommended Checkpoint Before Slice 0

Before implementing production code slices, the team should create an agreed
checkpoint:

- commit the current intended baseline, or
- create a branch that preserves the current dirty state, or
- explicitly document which dirty files are accepted baseline changes.

This is especially important because the repository has recently removed legacy
prototype runtime code and introduced the production backend layout.

## Handoff Requirements

Every code slice handoff should include:

- files intentionally changed,
- files noticed as pre-existing dirty state if relevant,
- whether any same-file pre-existing edits were present,
- commands run,
- remaining dirty state that belongs to the slice.
