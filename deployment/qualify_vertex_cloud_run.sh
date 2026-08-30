#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

PROJECT_ID="wexspace-agentic-2026"
REGION="us-central1"
LOCATION="global"
SERVICE_NAME="wexspace-iew-agentic-fleet"
SERVICE_ACCOUNT_EMAIL="wexspace-cloud-run@wexspace-agentic-2026.iam.gserviceaccount.com"
EXPECTED_COMMIT="${EXPECTED_COMMIT:?Set EXPECTED_COMMIT to the verified successor commit}"
EXPECTED_TREE="${EXPECTED_TREE:?Set EXPECTED_TREE to the verified successor tree}"
REPOSITORY_DIR="${REPOSITORY_DIR:-${HOME}/wexspace-hackathon/wexspace-iew-agentic-fleet}"
EVIDENCE_BUCKET="${PROJECT_ID}-r07-evidence"
READBACK_DIR=""

cleanup() {
  if [[ -n "${READBACK_DIR}" && -d "${READBACK_DIR}" && "${READBACK_DIR}" == /tmp/* ]]; then
    rm -rf -- "${READBACK_DIR}"
  fi
}
trap cleanup EXIT

fail() {
  printf 'WEXSPACE_VERTEX_SUCCESSOR_BLOCKED: %s\n' "$1" >&2
  exit 2
}

for command_name in gcloud git curl python3 sha256sum tar; do
  command -v "${command_name}" >/dev/null 2>&1 || fail "missing command: ${command_name}"
done

[[ -d "${REPOSITORY_DIR}/.git" ]] || fail "canonical Cloud Shell repository is absent"
[[ -z "$(git -C "${REPOSITORY_DIR}" status --porcelain=v1)" ]] || fail "Cloud Shell repository has uncommitted changes"
git -C "${REPOSITORY_DIR}" fetch --quiet origin main
[[ "$(git -C "${REPOSITORY_DIR}" rev-parse refs/remotes/origin/main)" == "${EXPECTED_COMMIT}" ]] || fail "remote main differs from the verified successor"
git -C "${REPOSITORY_DIR}" checkout --quiet --detach "${EXPECTED_COMMIT}"
[[ "$(git -C "${REPOSITORY_DIR}" rev-parse 'HEAD^{tree}')" == "${EXPECTED_TREE}" ]] || fail "successor tree mismatch"

[[ "$(gcloud projects describe "${PROJECT_ID}" --format='value(projectId)')" == "${PROJECT_ID}" ]] || fail "verified project is inaccessible"
[[ "$(gcloud config get-value project 2>/dev/null)" == "${PROJECT_ID}" ]] || gcloud config set project "${PROJECT_ID}" >/dev/null

cd "${REPOSITORY_DIR}"
python3 -m compileall -q src tests
GOOGLE_CLOUD_PROJECT="${PROJECT_ID}" \
CLOUD_RUN_REGION="${REGION}" \
GOOGLE_CLOUD_LOCATION="${LOCATION}" \
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL}" \
  bash deployment/deploy_cloud_run.sh

DEPLOY_TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_ROOT="${HOME}/wexspace-hackathon/cloud-gate7-evidence"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${DEPLOY_TIMESTAMP}-vertex-successor"
mkdir -p -- "${EVIDENCE_DIR}"

gcloud run services describe "${SERVICE_NAME}" --project "${PROJECT_ID}" --region "${REGION}" --format=json > "${EVIDENCE_DIR}/service.json"
SERVICE_URL="$(python3 - "${EVIDENCE_DIR}/service.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["status"]["url"])
PY
)"
READY_REVISION="$(python3 - "${EVIDENCE_DIR}/service.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["status"]["latestReadyRevisionName"])
PY
)"
[[ -n "${SERVICE_URL}" && -n "${READY_REVISION}" ]] || fail "Cloud Run service metadata is incomplete"

gcloud run revisions describe "${READY_REVISION}" --project "${PROJECT_ID}" --region "${REGION}" --format=json > "${EVIDENCE_DIR}/revision.json"
gcloud builds list --project "${PROJECT_ID}" --sort-by='~createTime' --limit=3 --format=json > "${EVIDENCE_DIR}/recent-builds.json"

python3 - "data/UTL-NET-001_SYNTHETIC_INPUT.json" "${EVIDENCE_DIR}/request.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as source:
    engineering_input = json.load(source)
payload = {
    "goal": "Analyze synthetic cooling-water network",
    "engineering_input": engineering_input,
    "asynchronous": False,
}
with open(sys.argv[2], "w", encoding="utf-8") as target:
    json.dump(payload, target, indent=2, sort_keys=True)
    target.write("\n")
PY

ADK_HTTP="$(curl --silent --show-error --max-time 600 \
  --header 'Content-Type: application/json' \
  --data-binary "@${EVIDENCE_DIR}/request.json" \
  --output "${EVIDENCE_DIR}/adk-live.json" \
  --write-out '%{http_code}' \
  "${SERVICE_URL}/adk/live")"

gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME} AND resource.labels.revision_name=${READY_REVISION}" \
  --project "${PROJECT_ID}" --freshness=30m --limit=50 --order=desc --format=json \
  > "${EVIDENCE_DIR}/cloud-run-logs.json"

python3 - "${EVIDENCE_DIR}" "${PROJECT_ID}" "${SERVICE_NAME}" "${REGION}" "${SERVICE_URL}" "${READY_REVISION}" "${EXPECTED_COMMIT}" "${EXPECTED_TREE}" "${ADK_HTTP}" "${SERVICE_ACCOUNT_EMAIL}" <<'PY'
import json, pathlib, sys

root = pathlib.Path(sys.argv[1])
(project, service, region, url, revision, commit, tree, adk_http, expected_service_account) = sys.argv[2:]
load = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
service_doc = load("service.json")
revision_doc = load("revision.json")
adk = load("adk-live.json")
logs = load("cloud-run-logs.json")

required_agents = {
    "wexspace_governing_agent",
    "iew_engineering_specialist",
    "wexspace_verification_evidence_specialist",
}
required_tools = {
    "govern_engineering_request",
    "run_hydraulic_calculation",
    "independently_verify_hydraulics",
}
adk_agents = {event.get("author") for event in adk.get("events", [])}
adk_tools = {
    call.get("name")
    for event in adk.get("events", [])
    for call in event.get("function_calls", [])
}
route = adk.get("execution_route", {})
containers = service_doc.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
env_entries = containers[0].get("env", []) if containers else []
env_names = {entry.get("name") for entry in env_entries}
service_account = service_doc.get("spec", {}).get("template", {}).get("spec", {}).get("serviceAccountName")

requalified_checks = {
    "adk_agents_present": required_agents <= adk_agents,
    "adk_http_200": adk_http == "200",
    "adk_model": adk.get("model") == "gemini-3.7-flash",
    "adk_pass": adk.get("passed") is True and adk.get("status") == "PASS",
    "adk_tools_present": required_tools <= adk_tools,
}
vertex_assertions = {
    "backend_vertex_ai": route.get("backend") == "VERTEX_AI",
    "adc_identity": route.get("credential_source") == "APPLICATION_DEFAULT_CREDENTIALS",
    "project": route.get("project") == project,
    "location": route.get("location") == "global",
    "api_key_not_required": route.get("api_key_required") is False,
    "api_key_env_absent": not ({"GOOGLE_API_KEY", "GEMINI_API_KEY"} & env_names),
    "service_account": service_account == expected_service_account,
    "logs_present": isinstance(logs, list) and len(logs) > 0,
}
passed = all(requalified_checks.values()) and all(vertex_assertions.values())
summary = {
    "artifact_id": "WEXSPACE-R07-VERTEX-CLOUD-RUN-SUCCESSOR_RESULT_R01",
    "project_id": project,
    "service_name": service,
    "region": region,
    "service_url": url,
    "ready_revision": revision,
    "successor_commit": commit,
    "successor_tree": tree,
    "http_status": {"adk_live": int(adk_http)},
    "model": adk.get("model"),
    "execution_route": route,
    "requalified_checks": requalified_checks,
    "vertex_assertions": vertex_assertions,
    "cloud_gate": "PASS" if passed else "FAIL",
    "first_technical_victory": "PASS_7_OF_7" if passed else "IN_PROGRESS_6_OF_7",
    "historical_developer_api_429_route": "SUPERSEDED_NOT_RETRIED",
    "secret_values_logged": False,
    "final_submit_performed": False,
}
(root / "VERTEX_SUCCESSOR_RESULT.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
if not passed:
    failed = [key for key, value in {**requalified_checks, **vertex_assertions}.items() if not value]
    raise SystemExit("Vertex successor failed checks: " + ", ".join(sorted(failed)))
PY

(
  cd "${EVIDENCE_DIR}"
  sha256sum *.json > SHA256SUMS.txt
  sha256sum -c SHA256SUMS.txt >/dev/null
)

EVIDENCE_ARCHIVE="${EVIDENCE_ROOT}/WEXSPACE-R07-VERTEX-CLOUD-RUN-EVIDENCE_${DEPLOY_TIMESTAMP}.tar.gz"
tar -czf "${EVIDENCE_ARCHIVE}" -C "${EVIDENCE_DIR}" .
EVIDENCE_ARCHIVE_SHA256="$(sha256sum "${EVIDENCE_ARCHIVE}" | awk '{print $1}')"
EVIDENCE_OBJECT="gate7/$(basename "${EVIDENCE_ARCHIVE}")"

if ! gcloud storage buckets describe "gs://${EVIDENCE_BUCKET}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${EVIDENCE_BUCKET}" --project "${PROJECT_ID}" --location "${REGION}" --uniform-bucket-level-access >/dev/null
fi
gcloud storage cp "${EVIDENCE_ARCHIVE}" "gs://${EVIDENCE_BUCKET}/${EVIDENCE_OBJECT}" \
  --custom-metadata="sha256=${EVIDENCE_ARCHIVE_SHA256}" >/dev/null

READBACK_DIR="$(mktemp -d)"
gcloud storage cp "gs://${EVIDENCE_BUCKET}/${EVIDENCE_OBJECT}" "${READBACK_DIR}/evidence-readback.tar.gz" >/dev/null
READBACK_SHA256="$(sha256sum "${READBACK_DIR}/evidence-readback.tar.gz" | awk '{print $1}')"
[[ "${READBACK_SHA256}" == "${EVIDENCE_ARCHIVE_SHA256}" ]] || fail "Cloud Storage raw readback SHA-256 mismatch"

python3 - "${EVIDENCE_DIR}/VERTEX_SUCCESSOR_RESULT.json" "gs://${EVIDENCE_BUCKET}/${EVIDENCE_OBJECT}" "${EVIDENCE_ARCHIVE_SHA256}" <<'PY'
import json, sys
summary = json.load(open(sys.argv[1], encoding="utf-8"))
pointer = {
    "artifact_id": "WEXSPACE-R07-VERTEX-CLOUD-RUN-EVIDENCE-POINTER_R01",
    "cloud_result": summary,
    "evidence_uri": sys.argv[2],
    "evidence_archive_sha256": sys.argv[3],
    "cloud_storage_raw_readback_sha256_verified": True,
}
print("=== WEXSPACE_VERTEX_SUCCESSOR_RESULT_BEGIN ===")
print(json.dumps(pointer, indent=2, sort_keys=True))
print("=== WEXSPACE_VERTEX_SUCCESSOR_RESULT_END ===")
PY
