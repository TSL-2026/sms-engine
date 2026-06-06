#!/usr/bin/env bash
# Deploy the alert processor Cloud Function
set -euo pipefail

PROJECT="safety-monitor-2026"
REGION="us-central1"
SERVICE_URL="https://sms-engine-660696925387.us-central1.run.app"

if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
  echo "ERROR: SLACK_WEBHOOK_URL not set"
  echo "Usage: SLACK_WEBHOOK_URL=https://hooks.slack.com/services/... ./deploy-alert-processor.sh"
  exit 1
fi

echo "Deploying alert-processor Cloud Function..."
gcloud functions deploy alert-processor \
  --gen2 \
  --runtime=python312 \
  --region=$REGION \
  --project=$PROJECT \
  --source=cloud-functions/alert-processor \
  --entry-point=main \
  --trigger-topic=monitoring-alerts \
  --set-env-vars="SERVICE_URL=$SERVICE_URL,SLACK_WEBHOOK_URL=$SLACK_WEBHOOK_URL" \
  --service-account="sms-engine-tester@safety-monitor-2026.iam.gserviceaccount.com"

echo "Done. Function will receive Monitoring alerts via Pub/Sub topic 'monitoring-alerts'."
