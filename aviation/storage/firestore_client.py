import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List


class FirestoreStorage:
    """Persistent storage for SMS-Engine assessments"""

    def __init__(self):
        self.db = None
        self.use_firestore = False

        if os.getenv("ENV") == "production":
            try:
                from google.cloud import firestore
                self.db = firestore.Client()
                self.use_firestore = True
            except Exception as e:
                import logging
                logging.getLogger("sms.storage").warning(
                    "Firestore unavailable, falling back to local storage: %s", e
                )

        self.collection = "flight_assessments"
        self._local_dir = "aviation_logs"
        os.makedirs(self._local_dir, exist_ok=True)

    def save_assessment(self, assessment: Dict[str, Any]):
        """Save assessment to Firestore or local fallback"""
        ts = assessment.get("timestamp", datetime.now(timezone.utc).isoformat())
        score = assessment.get("risk_score", 0)
        doc_id = f"{ts}_{score}"

        if self.use_firestore:
            self.db.collection(self.collection).document(doc_id).set(assessment)
        else:
            safe_id = doc_id.replace(":", "_").replace(".", "_")
            path = f"{self._local_dir}/{safe_id}.json"
            with open(path, "w") as f:
                json.dump(assessment, f, indent=2)

    def get_recent(self, limit: int = 100) -> List[Dict]:
        """Get recent assessments"""
        if self.use_firestore:
            from google.cloud import firestore
            docs = (
                self.db.collection(self.collection)
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            return [doc.to_dict() for doc in docs]
        return []
