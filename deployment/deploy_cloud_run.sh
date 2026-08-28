#!/usr/bin/env bash
set -euo pipefail

: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT to an approved billing-enabled project ID}"
: "${CLOUD_RUN_REGION:?Set CLOUD_RUN_REGION, for example us-central1}"
: "${GOOGLE_API_KEY_SECRET:?Set GOOGLE_API_KEY_SECRET to an existing Secret Manager secret name}"

SERVICE_NAME="wexspace-iew-agentic-fleet"

gcloud run deploy "${SERVICE_NAME}" \
  --project "${GOOGLE_CLOUD_PROJECT}" \
  --region "${CLOUD_RUN_REGION}" \
  --source . \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 1 \
  --memory 512Mi \
  --cpu 1 \
  --set-secrets "GOOGLE_API_KEY=${GOOGLE_API_KEY_SECRET}:latest"
