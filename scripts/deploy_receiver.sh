#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# GitSentry - Cloud Run Deployment Script for Webhook Receiver
# =============================================================================

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="gitsentry-webhook-receiver"
TOPIC_NAME="pr-events"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "=== Deploying GitSentry Webhook Receiver to Google Cloud Run ==="
echo "Project ID:  ${PROJECT_ID}"
echo "Region:      ${REGION}"
echo "Service:     ${SERVICE_NAME}"
echo "Topic:       ${TOPIC_NAME}"

# 1. Enable Required GCP APIs
echo "--> Enabling GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    secretmanager.googleapis.com \
    pubsub.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    --project="${PROJECT_ID}"

# 2. Create Pub/Sub Topic if not exists
echo "--> Verifying Pub/Sub Topic '${TOPIC_NAME}'..."
if ! gcloud pubsub topics describe "${TOPIC_NAME}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    echo "Creating Pub/Sub topic ${TOPIC_NAME}..."
    gcloud pubsub topics create "${TOPIC_NAME}" --project="${PROJECT_ID}"
fi

# 3. Build & Submit Container Image via Google Cloud Build
echo "--> Building container image with Cloud Build..."
gcloud builds submit --tag "${IMAGE_NAME}" \
    --file="services/receiver/Dockerfile" \
    --project="${PROJECT_ID}" .

# 4. Deploy to Cloud Run
echo "--> Deploying service to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_NAME}" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID},PUBSUB_TOPIC_PR_EVENTS=${TOPIC_NAME}" \
    --set-secrets="GITHUB_WEBHOOK_SECRET=github-webhook-secret:latest" \
    --min-instances=0 \
    --max-instances=10 \
    --memory=512Mi \
    --cpu=1 \
    --project="${PROJECT_ID}"

RECEIVER_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform=managed --region="${REGION}" --project="${PROJECT_ID}" --format='value(status.url)')

echo ""
echo "=================================================================="
echo " GitSentry Webhook Receiver Successfully Deployed!"
echo " Webhook URL: ${RECEIVER_URL}/webhook"
echo " Configure this URL in your GitHub App settings."
echo "=================================================================="
