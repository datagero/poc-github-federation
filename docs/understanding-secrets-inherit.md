# Understanding `secrets: inherit`

This document demonstrates a common misconception: `secrets: inherit` passes the caller's secrets to a reusable workflow, not the callee's own repo secrets.

## Demo Workflow

- File: `.github/workflows/reusable-internal.yml`
- Trigger: `workflow_call`
- Secrets:
  - `CALLER_SECRET` (optional): provided by the caller when using `secrets: inherit`

The workflow attempts two reads:
1. Read `CALLER_SECRET` (works when provided by caller)
2. Read `BAR_INTERNAL_SECRET` (defined only in bar) — not available when invoked via `workflow_call`

## What you might expect vs what happens

| What you might expect                 | What actually happens                 |
| ------------------------------------- | ------------------------------------- |
| Bar gets its own secrets              | Bar gets caller (foo)'s secrets       |
| `secrets: inherit` = callee's secrets | `secrets: inherit` = caller's secrets |

Why: GitHub Actions executes reusable workflows in the caller's context. The callee repo provides the workflow code, but secrets come from the caller.

## Solutions for true callee-owned credentials

1. OIDC federation (no stored secrets)
2. GitHub App tokens (installed on the callee repo)
3. Environment secrets (scoped to environments in the callee)
