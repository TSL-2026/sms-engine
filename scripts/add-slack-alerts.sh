#!/bin/bash
# Run this when you have a real Slack webhook URL
# Usage: ./scripts/add-slack-alerts.sh https://hooks.slack.com/services/xxx/yyy/zzz

set -euo pipefail

if [ -z "$1" ]; then
  echo "Usage: $0 https://hooks.slack.com/services/xxx/yyy/zzz"
  exit 1
fi

SLACK_URL=$1
PROJECT="safety-monitor-2026"
REGION="us-central1"
TOPIC="monitoring-alerts"

# Create Slack notification channel
CHANNEL_ID=$(gcloud beta monitoring channels create \
  --display-name="SMS-Engine Slack Alerts" \
  --type=slack \
  --channel-labels=channel-name="#sms-engine-alerts",webhook-url="$SLACK_URL" \
  --format='value(name)' 2>&1)

echo "Created notification channel: $CHANNEL_ID"

# Attach channel to alert policies
for POLICY in $(gcloud alpha monitoring policies list \
  --filter='displayName:("SMS-Engine API Downtime" OR "SMS-Engine High Error Rate")' \
  --format='value(name)' 2>&1); do
  echo "Updating policy: $POLICY"
  gcloud alpha monitoring policies update "$POLICY" \
    --add-notification-channels="$CHANNEL_ID" 2>&1 || true
done

# Update Cloud Function with real Slack URL
gcloud config set account thsafetylayer@gmail.com 2>/dev/null || true
gcloud functions deploy sms-engine-alert-processor \
  --update-env-vars="SLACK_WEBHOOK_URL=$SLACK_URL" \
  --runtime=python312 \
  --trigger-topic="$TOPIC" \
  --region="$REGION" \
  --source=cloud-functions/alert-processor \
  --entry-point=main 2>&1

echo "Slack alerts configured!"
