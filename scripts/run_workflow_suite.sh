#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-datagero/poc-github-federation}"

require() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require gh

run_and_watch() {
  local workflow_file="$1"

  echo ""
  echo "==> Triggering: ${workflow_file}"
  gh workflow run "${workflow_file}" -R "${REPO}" >/dev/null

  # The run may take a moment to appear in the list.
  local run_id=""
  for _ in {1..20}; do
    run_id="$(gh run list -R "${REPO}" --workflow "${workflow_file}" --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || true)"
    if [[ -n "${run_id}" && "${run_id}" != "null" ]]; then
      break
    fi
    sleep 1
  done

  if [[ -z "${run_id}" || "${run_id}" == "null" ]]; then
    echo "Could not find the run that was just triggered for ${workflow_file}." >&2
    exit 1
  fi

  local url
  url="$(gh run view "${run_id}" -R "${REPO}" --json url -q '.url')"
  echo "Run: ${url}"

  # Stream logs until completion; exits non-zero if the run fails.
  gh run watch "${run_id}" -R "${REPO}" --exit-status

  local conclusion
  conclusion="$(gh run view "${run_id}" -R "${REPO}" --json conclusion -q '.conclusion')"
  echo "Conclusion: ${conclusion}"
}

echo "Repo: ${REPO}"
echo "Triggering workflow suite (sequential)..."

run_and_watch "aws-oidc-minimal-test.yml"
run_and_watch "call-remote-workflow.yml"
run_and_watch "call-remote-oidc-sts-test.yml"

echo ""
echo "All workflows completed."


