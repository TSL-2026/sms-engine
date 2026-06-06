# ============================================================
# File: aviation/risk/audit_logger.py
# Version: v1.0.0
# Aviation Decision Audit Logger (SMS Traceability Layer)
# ============================================================

import json
import os
from datetime import datetime, timezone


class DecisionAuditLogger:
    """
    Stores every aviation decision for traceability (SMS-style logging)
    """

    def __init__(self, log_dir="aviation_logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def log(self, record: dict):
        timestamp = datetime.now(timezone.utc).isoformat()

        record_with_meta = {
            "timestamp_utc": timestamp,
            "system": "aviation_ai_dispatcher_v1.3",
            "data": record
        }

        filename = f"{self.log_dir}/decision_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(record_with_meta, f, indent=2)

        return filename