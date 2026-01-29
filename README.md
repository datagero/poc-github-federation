## GitHub workflow federation POC (entry point)

This repo is the **caller** in a “federated workflows” POC:
- It triggers **reusable workflows** that live in `datagero/poc-github-federation-dp`
- It demonstrates **secret forwarding** and **OIDC (AWS) from the caller identity**

### Prereqs

- **GitHub CLI**: `gh` installed + authenticated (`gh auth login`)
- **Repo variable**: `AWS_ACCOUNT_ID` set in `datagero/poc-github-federation`
- **IAM role**: `arn:aws:iam::${AWS_ACCOUNT_ID}:role/gh-oidc-poc-github-federation` trusts GitHub OIDC for the **base repo**

### Workflows (what they prove + expected output)

- **`AWS OIDC Minimal Test`** (`.github/workflows/aws-oidc-minimal-test.yml`)
  - **Proves**: base repo can assume the AWS role via OIDC
  - **Expected**: `aws sts get-caller-identity` succeeds and prints an ARN

- **`Remote call - secret forwarding proof`** (`.github/workflows/call-remote-workflow.yml`)
  - **Proves**: caller can pass a secret into a remote reusable workflow and the remote can prove it received it
  - **Expected**:
    - Remote prints the secret as `***` (masked)
    - Remote prints `Secret sha256: ...` and `Secret length: ...`
    - Caller summary prints “Local secret proof” and “Remote secret proof”
    - Note: with `GITHUB_TOKEN`, local vs remote proofs may differ because tokens can be **per-job**

- **`OIDC (base) -> remote reusable (STS)`** (`.github/workflows/call-remote-oidc-sts-test.yml`)
  - **Proves**: a remote reusable workflow can perform AWS OIDC using the **caller repo identity**
  - **Expected**: `Base STS ARN` equals `Remote STS ARN` and prints `✅ Same identity observed in base + remote`

### Run everything (recommended)

Use the script below to trigger the workflow suite and wait for each run to finish:

```bash
./scripts/run_workflow_suite.sh
```


