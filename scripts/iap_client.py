#!/usr/bin/env python3
"""
Final IAP Client for SMS-Engine using auto-created OAuth client
"""

import requests
import subprocess
import json
import os
from typing import Dict, Optional


class SMSEngineClient:
    """Production client for IAP-protected SMS-Engine"""

    IAP_CLIENT_ID = "660696925387-rk1ffklc4bcje0toq2psnqf3kv24ujdn.apps.googleusercontent.com"

    def __init__(self, service_url: str):
        self.service_url = service_url.rstrip("/")

    def _get_iap_token(self) -> str:
        cmd = [
            "gcloud", "auth", "print-identity-token",
            "--audiences", self.IAP_CLIENT_ID,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Token failed: {result.stderr}")
        return result.stdout.strip()

    def request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        token = self._get_iap_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        url = f"{self.service_url}{endpoint}"

        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json() if response.content else {}

    def health(self) -> Dict:
        return self.request("GET", "/")

    def safety_report(self) -> Dict:
        return self.request("GET", "/safety-report")

    def assess_flight(self, scenario: str) -> Dict:
        raw = self.request("POST", "/assess-flight", {"scenario": scenario})
        return raw.get("result", raw)

    def simulate(self, scenarios: list) -> Dict:
        return self.request("POST", "/simulate", {"scenarios": scenarios})


if __name__ == "__main__":
    SERVICE_URL = "https://sms-engine-660696925387.us-central1.run.app"
    client = SMSEngineClient(SERVICE_URL)

    print("Testing IAP-authenticated SMS-Engine\n")

    print("1. Health:")
    print(f"   {client.health()}\n")

    print("2. Safety Report:")
    report = client.safety_report()
    m = report.get("metrics", {})
    print(f"   Assessments: {m.get('total_assessments', 0)}")
    print(f"   GO: {m.get('go_no_go_decisions', {}).get('GO', 0)}")
    print(f"   NO-GO: {m.get('go_no_go_decisions', {}).get('NO-GO', 0)}\n")

    print("3. Low Risk Flight:")
    low = client.assess_flight("Pilot rested, day VFR, familiar airport")
    d = low.get("decision", {})
    print(f"   Decision: {d.get('state')}")
    print(f"   Risk Score: {d.get('risk_score')}/25\n")

    print("4. High Risk Flight:")
    high = client.assess_flight(
        "Pilot fatigued 16hrs, night IMC, mountain terrain "
        "aircraft maintenance deferred"
    )
    d = high.get("decision", {})
    print(f"   Decision: {d.get('state')}")
    print(f"   Risk Score: {d.get('risk_score')}/25\n")

    print("5. Batch Simulation:")
    batch = client.simulate([
        "Day VFR, pilot current",
        "Night IMC, low fuel",
        "Mountain airport, high winds",
    ])
    print(f"   Processed: {len(batch.get('results', []))} scenarios\n")

    print("All endpoints working behind IAP!")
