#!/usr/bin/env bash
set -euo pipefail

GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-wexspace-agentic-2026}"
CLOUD_RUN_REGION="${CLOUD_RUN_REGION:-us-central1}"
GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"
SERVICE_NAME="wexspace-iew-agentic-fleet"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-wexspace-cloud-run@wexspace-agentic-2026.iam.gserviceaccount.com}"

if [[ "${GOOGLE_CLOUD_PROJECT}" != "wexspace-agentic-2026" ]]; then
  echo "Refusing to deploy outside the verified competition project." >&2
  exit 2
fi

gcloud run deploy "${SERVICE_NAME}" \
  --project "${GOOGLE_CLOUD_PROJECT}" \
  --region "${CLOUD_RUN_REGION}" \
  --source . \
  --allow-unauthenticated \
  --service-account "${SERVICE_ACCOUNT_EMAIL}" \
  --min-instances 0 \
  --max-instances 1 \
  --memory 512Mi \
  --cpu 1 \
  --update-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}" \
  --remove-env-vars "GEMINI_API_KEY" \
  --remove-secrets "GOOGLE_API_KEY" \
  --quiet
