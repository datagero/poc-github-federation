## GitHub workflow federation POC (entry point)

This repo is the **caller** in a “federated workflows” POC:
- It triggers **reusable workflows** that live in `datagero/poc-github-federation-dp`
- It demonstrates **secret forwarding** and **OIDC (AWS) from the caller identity**

### Reusable workflow: caller-provided credentials (TASK-001-1)

This repo also provides a reusable workflow that accepts secrets from the caller (so the caller keeps ownership of credentials).

- **Reusable workflow**: `.github/workflows/reusable-deploy.yml`
- **Trigger**: `workflow_call`
- **Inputs**:
  - `environment` (required)
- **Secrets**:
  - `DEPLOY_TOKEN` (required, provided by the caller)

**Security note**: the workflow never prints the secret; it only logs a length + sha256 proof.


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



### CSV/QIF Column Mapper (SCRUM-8)

- Purpose: Normalize bank exports (`.csv` or `.qif`) into a standard schema with a one-time header mapping saved as a reusable "Bank Profile".
- Script: `scripts/csv_mapper.py`

Quick start:

```bash
python3 scripts/csv_mapper.py samples/transactions_sample.csv --bank-name BarBank --output normalized.csv
```

What happens:
- If headers are unknown, the tool interactively asks you to map `date`, `description`, and `amount`.
- The mapping is saved under `.bank-profiles/BarBank.json` (and a header-signature profile), so future files from the same bank map automatically.
- Use `--output` to write a normalized CSV with columns: `date,description,amount`. Without `--output`, JSON lines are printed to stdout.

Supports `.csv` and `.qif` inputs.


