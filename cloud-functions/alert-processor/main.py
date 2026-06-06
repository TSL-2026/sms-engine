#!/usr/bin/env python3
"""
Alert Processor for SMS-Engine
Triggered by Monitoring alerts via Pub/Sub.
Fetches latest safety metrics and posts enriched context to Slack.
"""

import json
import os
import base64
import requests
from datetime import datetime, timezone


SERVICE_URL = os.getenv("SERVICE_URL", "https://sms-engine-660696925387.us-central1.run.app")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")
IAP_AUDIENCE = "660696925387-rk1ffklc4bcje0toq2psnqf3kv24ujdn.apps.googleusercontent.com"
METADATA_URL = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"


def get_iap_token():
    """Get IAP token from GCE metadata server."""
    headers = {"Metadata-Flavor": "Google"}
    params = {"audience": IAP_AUDIENCE, "format": "full"}
    resp = requests.get(METADATA_URL, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    return resp.text


def fetch_safety_report(token):
    """Get current safety metrics from SMS-Engine."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{SERVICE_URL}/safety-report", headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def format_slack_message(alert, report):
    """Build a rich Slack message with alert context and metrics."""
    metrics = report.get("metrics", {})
    decisions = metrics.get("go_no_go_decisions", {})

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"⚠️ {alert.get('alertName', 'SMS-Engine Alert')}"}
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Service:* SMS-Engine\n"
                    f"*Time:* {datetime.now(timezone.utc).isoformat()}\n"
                    f"*Severity:* {alert.get('severity', 'N/A')}\n"
                    f"*Condition:* {alert.get('conditionName', 'N/A')}"
                )
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Current Safety Metrics:*\n"
                    f"• Total Assessments: {metrics.get('total_assessments', 'N/A')}\n"
                    f"• GO (Cleared): {decisions.get('GO', 0)}\n"
                    f"• NO-GO (Blocked): {decisions.get('NO-GO', 0)}\n"
                    f"• Conditional: {decisions.get('CONDITIONAL', 0)}\n"
                    f"• Active Alerts: {report.get('total_alerts', 0)}"
                )
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Open Dashboard"},
                    "url": f"{SERVICE_URL}/dashboard/"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View in GCP Console"},
                    "url": "https://console.cloud.google.com/monitoring?project=safety-monitor-2026"
                }
            ]
        }
    ]

    return {"text": f"SMS-Engine Alert: {alert.get('alertName', '')}", "blocks": blocks}


def main(event, context):
    """Cloud Function entry point."""
    pubsub_data = base64.b64decode(event.get("data", "")).decode("utf-8")
    alert = json.loads(pubsub_data)

    token = get_iap_token()
    report = fetch_safety_report(token)

    if SLACK_WEBHOOK:
        message = format_slack_message(alert, report)
        requests.post(SLACK_WEBHOOK, json=message, timeout=10)
        print("Slack notification sent.")
    else:
        print("No SLACK_WEBHOOK_URL configured.")
        print(f"Alert: {alert.get('alertName', 'Unknown')}")
        print(f"Metrics: {json.dumps(report, indent=2)}")


if __name__ == "__main__":
    # Local test
    test_alert = {"alertName": "Uptime Check Failed", "severity": "CRITICAL", "conditionName": "API endpoint unreachable"}
    main({"data": base64.b64encode(json.dumps(test_alert).encode()).decode()}, None)
