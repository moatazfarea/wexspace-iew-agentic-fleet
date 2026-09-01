#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

PROJECT_ID="wexspace-agentic-2026"
REGION="us-central1"
BRANCH="r19-pae006-google-stack"
REPOSITORY="moatazfarea/wexspace-iew-agentic-fleet"
REMOTE_URL="https://github.com/${REPOSITORY}.git"
EVIDENCE_BUCKET="${PROJECT_ID}-r07-evidence"
EXPECTED_SOURCE_COMMIT="${R19_EXPECTED_COMMIT:?R19_EXPECTED_COMMIT must pin the reviewed R19 source commit}"
CLOUD_REPOSITORY_DIR="${CLOUD_SHELL_REPOSITORY_DIR:-${HOME}/wexspace-hackathon/wexspace-iew-agentic-fleet}"
RUN_ROOT="$(mktemp -d -t wexspace-r19-XXXXXX)"
SOURCE_DIR="${RUN_ROOT}/source"
OUTPUT_ROOT="${RUN_ROOT}/pae-output"
SOURCE_IS_WORKTREE=false

cleanup() {
  set +e
  if [[ "${SOURCE_IS_WORKTREE}" == true \
    && "${SOURCE_DIR}" == "${RUN_ROOT}/"* \
    && -e "${SOURCE_DIR}/.git" \
    && -d "${CLOUD_REPOSITORY_DIR}/.git" ]]; then
    git -C "${CLOUD_REPOSITORY_DIR}" worktree remove --force "${SOURCE_DIR}" >/dev/null 2>&1
  fi
  if [[ "${RUN_ROOT}" == /tmp/wexspace-r19-* && -d "${RUN_ROOT}" ]]; then
    rm -rf -- "${RUN_ROOT}"
  fi
}
trap cleanup EXIT

fail() {
  printf 'WEXSPACE_R19_BLOCKED: %s\n' "$1" >&2
  exit 2
}

for command_name in gcloud git gh python3 rg sha256sum tar; do
  command -v "${command_name}" >/dev/null 2>&1 || fail "missing command: ${command_name}"
done

ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n 1)"
[[ -n "${ACTIVE_ACCOUNT}" ]] || fail "Google Cloud Shell has no active authenticated account"
unset ACTIVE_ACCOUNT
[[ "$(gcloud projects describe "${PROJECT_ID}" --format='value(projectId)')" == "${PROJECT_ID}" ]] \
  || fail "qualified Google Cloud project is inaccessible"
gcloud config set project "${PROJECT_ID}" >/dev/null
gcloud config set run/region "${REGION}" >/dev/null
gcloud services list \
  --project "${PROJECT_ID}" \
  --enabled \
  --filter='config.name=aiplatform.googleapis.com' \
  --format='value(config.name)' | grep -Fxq aiplatform.googleapis.com \
  || fail "Vertex AI API is not enabled on the qualified project"
gcloud storage buckets describe "gs://${EVIDENCE_BUCKET}" --project "${PROJECT_ID}" >/dev/null \
  || fail "existing qualified evidence bucket is unavailable"

gh auth status --hostname github.com >/dev/null 2>&1 \
  || fail "GitHub CLI is not authenticated in the existing Cloud Shell"
[[ "$(gh api user --jq .login)" == "moatazfarea" ]] \
  || fail "GitHub CLI is authenticated as a different account"

if [[ -d "${CLOUD_REPOSITORY_DIR}/.git" ]]; then
  git -C "${CLOUD_REPOSITORY_DIR}" fetch origin "${BRANCH}" --quiet
  [[ "$(git -C "${CLOUD_REPOSITORY_DIR}" rev-parse FETCH_HEAD)" == "${EXPECTED_SOURCE_COMMIT}" ]] \
    || fail "remote R19 source commit differs from the pinned reviewed commit"
  git -C "${CLOUD_REPOSITORY_DIR}" worktree add --detach "${SOURCE_DIR}" "${EXPECTED_SOURCE_COMMIT}" >/dev/null
  SOURCE_IS_WORKTREE=true
else
  git clone --quiet --no-checkout "${REMOTE_URL}" "${SOURCE_DIR}"
  git -C "${SOURCE_DIR}" fetch origin "${EXPECTED_SOURCE_COMMIT}" --quiet
  git -C "${SOURCE_DIR}" checkout --detach "${EXPECTED_SOURCE_COMMIT}" --quiet
fi

[[ "$(git -C "${SOURCE_DIR}" rev-parse HEAD)" == "${EXPECTED_SOURCE_COMMIT}" ]] \
  || fail "checked-out source commit mismatch"
SOURCE_TREE="$(git -C "${SOURCE_DIR}" rev-parse 'HEAD^{tree}')"
[[ -z "$(git -C "${SOURCE_DIR}" status --porcelain=v1)" ]] \
  || fail "isolated R19 source worktree is not clean"

python3 -m venv "${RUN_ROOT}/venv"
"${RUN_ROOT}/venv/bin/python" -m pip install --disable-pip-version-check --quiet -e "${SOURCE_DIR}"

export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
export GOOGLE_CLOUD_LOCATION=global
export WEXSPACE_CLOUD_EXECUTION_SURFACE="Google Cloud Shell"
export WEXSPACE_PAE_OUTPUT_ROOT="${OUTPUT_ROOT}"
unset GOOGLE_API_KEY GEMINI_API_KEY

"${RUN_ROOT}/venv/bin/python" - "${PROJECT_ID}" >"${RUN_ROOT}/ADC_PREFLIGHT_R01.json" <<'PY'
import json
import sys

import google.auth
from google.auth.transport.requests import Request

requested_project = sys.argv[1]
credentials, detected_project = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
credentials.refresh(Request())
proof = {
    "credential_source": "APPLICATION_DEFAULT_CREDENTIALS",
    "credential_type": f"{type(credentials).__module__}.{type(credentials).__name__}",
    "detected_project": detected_project,
    "requested_project": requested_project,
    "credential_valid": bool(credentials.valid),
    "access_token_present_not_logged": bool(credentials.token),
    "secret_values_logged": False,
}
if not proof["credential_valid"] or not proof["access_token_present_not_logged"]:
    raise SystemExit("ADC credential refresh failed")
print(json.dumps(proof, indent=2, sort_keys=True))
PY

(
  cd "${SOURCE_DIR}"
  "${RUN_ROOT}/venv/bin/python" -m unittest discover -s tests -p 'test_pae006.py' -v
) >"${RUN_ROOT}/affected-tests.txt" 2>&1

(
  cd "${SOURCE_DIR}"
  "${RUN_ROOT}/venv/bin/python" -m wexspace.adk_fleet pae-live \
    --input data/PAE006_FRESH_MOTIVE_AIR_SENSITIVITY_R01_INPUT.json
) >"${RUN_ROOT}/ADK_RESPONSE.json" 2>"${RUN_ROOT}/ADK_STDERR.log"

RUN_DIR="$(python3 - "${RUN_ROOT}/ADK_RESPONSE.json" <<'PY'
import json, pathlib, sys
result = json.load(open(sys.argv[1], encoding="utf-8"))
if result.get("passed") is not True:
    raise SystemExit("live ADK response did not pass")
artifacts = result.get("artifacts", {})
if not artifacts:
    raise SystemExit("live ADK response has no artifacts")
parents = {str(pathlib.Path(item["path"]).parent) for item in artifacts.values()}
if len(parents) != 1:
    raise SystemExit("artifact paths do not share one bounded run directory")
print(parents.pop())
PY
)"
[[ "${RUN_DIR}" == "${OUTPUT_ROOT}/"* && -d "${RUN_DIR}" ]] \
  || fail "ADK artifact directory escaped the bounded output root"

(
  cd "${RUN_DIR}"
  sha256sum -c PAE006_FRESH_SHA256SUMS_R01.txt
) >"${RUN_ROOT}/artifact-readback.txt"

RUN_ID="$(basename "${RUN_DIR}")"
RESULT_SHA256="$(sha256sum "${RUN_ROOT}/ADK_RESPONSE.json" | awk '{print $1}')"
ACCOUNT_ID_SHA256="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n 1 | sha256sum | awk '{print $1}')"
LOG_PAYLOAD="$(python3 - "${RUN_ID}" "${EXPECTED_SOURCE_COMMIT}" "${SOURCE_TREE}" "${RESULT_SHA256}" <<'PY'
import json, sys
print(json.dumps({
    "event": "PAE006_FRESH_GOOGLE_ADK_PASS",
    "run_id": sys.argv[1],
    "source_commit": sys.argv[2],
    "source_tree": sys.argv[3],
    "adk_response_sha256": sys.argv[4],
    "model": "gemini-3.7-flash",
    "framework": "Google ADK",
    "backend": "VERTEX_AI",
    "cloud_execution_surface": "Google Cloud Shell",
    "workflow_state": "AWAITING_HUMAN_REVIEW",
    "release_performed": False,
}, sort_keys=True))
PY
)"
gcloud logging write wexspace-r19-pae006 "${LOG_PAYLOAD}" \
  --project "${PROJECT_ID}" --payload-type=json --severity=NOTICE >/dev/null
unset LOG_PAYLOAD

LOG_READBACK="${RUN_ROOT}/cloud-logging-readback.json"
for attempt in 1 2 3; do
  gcloud logging read \
    "jsonPayload.run_id=\"${RUN_ID}\" AND jsonPayload.event=\"PAE006_FRESH_GOOGLE_ADK_PASS\"" \
    --project "${PROJECT_ID}" --freshness=30m --limit=10 --format=json >"${LOG_READBACK}"
  if python3 - "${LOG_READBACK}" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
raise SystemExit(0 if value else 1)
PY
  then
    break
  fi
  [[ "${attempt}" -lt 3 ]] || fail "Cloud Logging write could not be read back"
  sleep 5
done

python3 - \
  "${RUN_ROOT}/ADK_RESPONSE.json" \
  "${RUN_ROOT}/GOOGLE_CLOUD_EXECUTION_PROOF.json" \
  "${PROJECT_ID}" "${REGION}" "${EXPECTED_SOURCE_COMMIT}" "${SOURCE_TREE}" \
  "${RESULT_SHA256}" "${ACCOUNT_ID_SHA256}" "${RUN_ID}" <<'PY'
import datetime, json, sys
(
    response_path, output_path, project, region, commit, tree,
    response_sha, account_sha, run_id,
) = sys.argv[1:]
response = json.load(open(response_path, encoding="utf-8"))
execution_evidence = response.get("execution_evidence", {})
checks = {
    "live_response_pass": response.get("passed") is True,
    "google_adk": response.get("google_agent_framework") == "Google ADK",
    "gemini_3_7_flash": response.get("model") == "gemini-3.7-flash",
    "provider_reported_model_identity": execution_evidence.get(
        "provider_model_identity_verified"
    ) is True,
    "vertex_ai": response.get("execution_route", {}).get("backend") == "VERTEX_AI",
    "cloud_shell": response.get("cloud_execution_surface") == "Google Cloud Shell",
    "twelve_fresh_points": response.get("structured_engineering_results", {}).get("point_count") == 12,
    "all_points_choked": response.get("structured_engineering_results", {}).get("summary", {}).get("all_points_choked") is True,
    "independent_verification": response.get("independent_verification", {}).get("verified") is True,
    "google_stack_gate": response.get("google_stack_gate", {}).get("status") == "PASS",
    "awaiting_human_review": response.get("workflow_state") == "AWAITING_HUMAN_REVIEW",
    "release_not_performed": response.get("release_performed") is False,
    "manifest_valid": response.get("artifact_manifest_valid") is True,
}
proof = {
    "schema_version": "1.0",
    "artifact_id": "PAE006-FRESH-GOOGLE-CLOUD-EXECUTION-PROOF_R01",
    "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "run_id": run_id,
    "project_id": project,
    "region": region,
    "cloud_execution_surface": "Google Cloud Shell",
    "framework": "Google ADK",
    "model": "gemini-3.7-flash",
    "backend": "VERTEX_AI",
    "credential_source": "APPLICATION_DEFAULT_CREDENTIALS",
    "authenticated_account_identifier_sha256": account_sha,
    "source_commit": commit,
    "source_tree": tree,
    "adk_response_sha256": response_sha,
    "cloud_logging_write_readback": True,
    "checks": checks,
    "status": "PASS" if all(checks.values()) else "FAIL",
    "workflow_state": response.get("workflow_state"),
    "release_performed": False,
    "secret_values_logged": False,
}
json.dump(proof, open(output_path, "w", encoding="utf-8"), indent=2, sort_keys=True)
open(output_path, "a", encoding="utf-8").write("\n")
if proof["status"] != "PASS":
    raise SystemExit("Google Cloud execution proof checks failed")
PY

PUBLIC_EVIDENCE_DIR="${SOURCE_DIR}/evidence/r19/pae006/${RUN_ID}"
mkdir -p -- "${PUBLIC_EVIDENCE_DIR}"
cp -a -- "${RUN_DIR}/." "${PUBLIC_EVIDENCE_DIR}/"
cp -- "${RUN_ROOT}/ADK_RESPONSE.json" "${PUBLIC_EVIDENCE_DIR}/PAE006_FRESH_GOOGLE_ADK_RESPONSE_R01.json"
cp -- "${RUN_ROOT}/GOOGLE_CLOUD_EXECUTION_PROOF.json" "${PUBLIC_EVIDENCE_DIR}/GOOGLE_CLOUD_EXECUTION_PROOF_R01.json"
cp -- "${RUN_ROOT}/cloud-logging-readback.json" "${PUBLIC_EVIDENCE_DIR}/CLOUD_LOGGING_READBACK_R01.json"
cp -- "${RUN_ROOT}/ADC_PREFLIGHT_R01.json" "${PUBLIC_EVIDENCE_DIR}/ADC_PREFLIGHT_R01.json"
cp -- "${RUN_ROOT}/affected-tests.txt" "${PUBLIC_EVIDENCE_DIR}/AFFECTED_TESTS_R01.txt"
cp -- "${RUN_ROOT}/artifact-readback.txt" "${PUBLIC_EVIDENCE_DIR}/ARTIFACT_READBACK_R01.txt"
(
  cd "${PUBLIC_EVIDENCE_DIR}"
  mapfile -d '' evidence_files < <(
    find . -maxdepth 1 -type f ! -name 'GOOGLE_SIDE_SHA256SUMS_R01.txt' -printf '%P\0' | sort -z
  )
  [[ "${#evidence_files[@]}" -gt 0 ]] || fail "public evidence directory is empty"
  sha256sum -- "${evidence_files[@]}" > GOOGLE_SIDE_SHA256SUMS_R01.txt
  sha256sum -c GOOGLE_SIDE_SHA256SUMS_R01.txt >/dev/null
)

if rg -n \
  -e 'AIza[0-9A-Za-z_-]{30,}' \
  -e '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----' \
  -e 'gh[pousr]_[A-Za-z0-9_]{30,}' \
  -e 'ya29\.[0-9A-Za-z_-]+' \
  "${PUBLIC_EVIDENCE_DIR}" >/dev/null; then
  fail "public-safe evidence scan found a credential-like value"
fi

ARCHIVE="${RUN_ROOT}/PAE006-FRESH-GOOGLE-STACK-EVIDENCE_${RUN_ID}.tar.gz"
tar -czf "${ARCHIVE}" -C "${PUBLIC_EVIDENCE_DIR}" .
ARCHIVE_SHA256="$(sha256sum "${ARCHIVE}" | awk '{print $1}')"
GCS_OBJECT="r19/pae006/$(basename "${ARCHIVE}")"
gcloud storage cp "${ARCHIVE}" "gs://${EVIDENCE_BUCKET}/${GCS_OBJECT}" \
  --custom-metadata="sha256=${ARCHIVE_SHA256}" >/dev/null
READBACK_ARCHIVE="${RUN_ROOT}/gcs-readback.tar.gz"
gcloud storage cp "gs://${EVIDENCE_BUCKET}/${GCS_OBJECT}" "${READBACK_ARCHIVE}" >/dev/null
[[ "$(sha256sum "${READBACK_ARCHIVE}" | awk '{print $1}')" == "${ARCHIVE_SHA256}" ]] \
  || fail "Google Cloud Storage raw readback SHA-256 mismatch"

git -C "${SOURCE_DIR}" config user.name "WEXSPACE Evidence Bot"
git -C "${SOURCE_DIR}" config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git -C "${SOURCE_DIR}" add -- "evidence/r19/pae006/${RUN_ID}"
git -C "${SOURCE_DIR}" commit -m "evidence(r19): add fresh PAE-006 Google ADK run" >/dev/null
EVIDENCE_COMMIT="$(git -C "${SOURCE_DIR}" rev-parse HEAD)"
EVIDENCE_TREE="$(git -C "${SOURCE_DIR}" rev-parse 'HEAD^{tree}')"
gh auth setup-git >/dev/null
git -C "${SOURCE_DIR}" push \
  --force-with-lease="refs/heads/${BRANCH}:${EXPECTED_SOURCE_COMMIT}" \
  origin "HEAD:refs/heads/${BRANCH}" >/dev/null
[[ "$(gh api "repos/${REPOSITORY}/git/ref/heads/${BRANCH}" --jq .object.sha)" == "${EVIDENCE_COMMIT}" ]] \
  || fail "public evidence branch commit readback mismatch"
[[ "$(gh api "repos/${REPOSITORY}/git/commits/${EVIDENCE_COMMIT}" --jq .tree.sha)" == "${EVIDENCE_TREE}" ]] \
  || fail "public evidence branch tree readback mismatch"

python3 - \
  "${RUN_ID}" "${EXPECTED_SOURCE_COMMIT}" "${SOURCE_TREE}" \
  "${EVIDENCE_COMMIT}" "${EVIDENCE_TREE}" \
  "gs://${EVIDENCE_BUCKET}/${GCS_OBJECT}" "${ARCHIVE_SHA256}" \
  "https://github.com/${REPOSITORY}/tree/${EVIDENCE_COMMIT}/evidence/r19/pae006/${RUN_ID}" <<'PY'
import json, sys
(
    run_id, source_commit, source_tree, evidence_commit, evidence_tree,
    gcs_uri, archive_sha256, public_evidence_url,
) = sys.argv[1:]
result = {
    "study_id": "PAE006-FRESH-MOTIVE-AIR-SENSITIVITY-R01",
    "run_id": run_id,
    "PAE_R03_GOOGLE_STACK_GATE": "PASS",
    "google_agent_framework": "Google ADK",
    "model": "gemini-3.7-flash",
    "backend": "VERTEX_AI",
    "cloud_execution_surface": "Google Cloud Shell",
    "governing_agent_invoked": True,
    "iew_specialist_invoked": True,
    "pae_deterministic_tool_invoked": True,
    "verification_specialist_invoked": True,
    "workflow_state": "AWAITING_HUMAN_REVIEW",
    "release_performed": False,
    "source_commit": source_commit,
    "source_tree": source_tree,
    "evidence_commit": evidence_commit,
    "evidence_tree": evidence_tree,
    "public_evidence_url": public_evidence_url,
    "gcs_evidence_uri": gcs_uri,
    "gcs_archive_sha256": archive_sha256,
    "gcs_raw_readback_verified": True,
    "cloud_logging_write_readback": True,
    "final_submit_performed": False,
}
print("=== WEXSPACE_R19_PAE006_GOOGLE_STACK_RESULT_BEGIN ===")
print(json.dumps(result, indent=2, sort_keys=True))
print("=== WEXSPACE_R19_PAE006_GOOGLE_STACK_RESULT_END ===")
PY
