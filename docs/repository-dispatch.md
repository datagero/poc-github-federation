# Repository Dispatch Handler

This workflow demonstrates asynchronous invocation with `repository_dispatch`.

- File: `.github/workflows/on-dispatch.yml`
- Trigger: `repository_dispatch` with types: `build-request`, `deploy-request`
- Behavior: Logs `github.event.action` and `client_payload`, then simulates work

## Payload

Example payload sent by the caller:

```json
{
  "ref": "<sha>",
  "triggered_by": "<actor>",
  "source_repo": "<owner/repo>",
  "source_run_id": "<run id>",
  "environment": "staging|production"
}
```

## Comparison with `workflow_call`

| Aspect     | `workflow_call`      | `repository_dispatch`          |
| ---------- | -------------------- | ------------------------------ |
| Execution  | Synchronous (inline) | Asynchronous (fire-and-forget) |
| Status     | Reflected in caller  | Separate workflow run          |
| Inputs     | Typed inputs/outputs | Freeform JSON payload          |
| Auth       | `GITHUB_TOKEN` works | Requires PAT                   |
| Visibility | Single run in caller | Two separate runs              |

## Notes

- For callee-owned credentials, prefer OIDC or environment secrets; dispatch is about async execution and requires a PAT on the caller side.
