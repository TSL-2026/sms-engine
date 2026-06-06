#!/usr/bin/env bash
set -euo pipefail

PROJECT="safety-monitor-2026"
REGION="us-central1"
SERVICE="sms-engine"
URL="https://sms-engine-660696925387.us-central1.run.app"

echo "=== 1. Enable APIs ==="
gcloud services enable monitoring.googleapis.com cloudfunctions.googleapis.com

echo "=== 2. Create uptime check ==="
gcloud monitoring uptime create "SMS-Engine API Health" \
  --resource-type="uptime-url" \
  --resource-labels="host=sms-engine-660696925387.us-central1.run.app" \
  --path="/" \
  --request-method="get" \
  --period=5 \
  --timeout=10

echo "=== 3. Create downtime alert ==="
gcloud alpha monitoring policies create \
  --policy-from-file="$(dirname "$0")/policy-downtime.json"

echo "=== 4. Create error rate alert ==="
gcloud alpha monitoring policies create \
  --policy-from-file="$(dirname "$0")/policy-errors.json"

echo "=== 5. Add Slack notification channel ==="
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  gcloud beta monitoring channels create \
    --display-name="sms-engine-alerts" \
    --type=slack \
    --channel-labels="channel-name=#sms-engine-alerts,webhook-url=$SLACK_WEBHOOK_URL"
  echo "   Slack channel created."
else
  echo "   Set SLACK_WEBHOOK_URL env var and re-run to add Slack notifications."
fi

echo "=== 6. Deploy alert processor Cloud Function ==="
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  bash "$(dirname "$0")/../cloud-functions/alert-processor/deploy.sh"
  echo "   Cloud Function deployed."
else
  echo "   Set SLACK_WEBHOOK_URL and run deploy.sh to deploy."
fi

echo ""
echo "Monitoring setup complete!"
echo "- Uptime check: every 5min to $URL/"
echo "- Downtime alert: CRITICAL if check fails for 120s"
echo "- Error rate alert: WARNING if 5xx > 5% over 5min"
