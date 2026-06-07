"""
Firestore database layer for SMS-Engine.
Uses local JSON fallback when Firestore is unavailable (dev mode).
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional
from sms_engine.config import settings

DB_DIR = "sms_db"


def _get_db():
    if settings.environment == "production":
        try:
            from google.cloud import firestore
            return firestore.Client(), True
        except Exception:
            pass
    os.makedirs(DB_DIR, exist_ok=True)
    return None, False


def _next_id(collection: str) -> str:
    return f"{collection}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"


def _local_path(collection: str, doc_id: str = "") -> str:
    if doc_id:
        return f"{DB_DIR}/{collection}_{doc_id}.json"
    return f"{DB_DIR}/{collection}.json"


class Collection:
    def __init__(self, name: str):
        self.name = name
        self.db, self.use_firestore = _get_db()

    def _firestore_collection(self):
        if self.use_firestore:
            return self.db.collection(self.name)
        return None

    def add(self, data: dict) -> str:
        doc_id = data.get("id") or _next_id(self.name)
        data["id"] = doc_id
        ts = datetime.now(timezone.utc).isoformat()
        if "created_at" not in data:
            data["created_at"] = ts

        col = self._firestore_collection()
        if col:
            col.document(doc_id).set(data)
        else:
            with open(_local_path(self.name, doc_id), "w") as f:
                json.dump(data, f, indent=2, default=str)
        return doc_id

    def update(self, doc_id: str, data: dict):
        col = self._firestore_collection()
        if col:
            col.document(doc_id).update(data)
        else:
            path = _local_path(self.name, doc_id)
            if os.path.exists(path):
                with open(path) as f:
                    existing = json.load(f)
                existing.update(data)
                with open(path, "w") as f:
                    json.dump(existing, f, indent=2, default=str)

    def get(self, doc_id: str) -> Optional[dict]:
        col = self._firestore_collection()
        if col:
            doc = col.document(doc_id).get()
            return doc.to_dict() if doc.exists else None
        path = _local_path(self.name, doc_id)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return None

    def list(self, filters: Optional[dict] = None) -> list[dict]:
        col = self._firestore_collection()
        if col:
            query = col
            if filters:
                for key, value in filters.items():
                    query = query.where(key, "==", value)
            return [doc.to_dict() for doc in query.stream()]
        import glob
        results = []
        for path in glob.glob(f"{DB_DIR}/{self.name}_*.json"):
            with open(path) as f:
                results.append(json.load(f))
        if filters:
            results = [r for r in results if all(r.get(k) == v for k, v in filters.items())]
        return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)

    def delete(self, doc_id: str):
        col = self._firestore_collection()
        if col:
            col.document(doc_id).delete()
        else:
            path = _local_path(self.name, doc_id)
            if os.path.exists(path):
                os.remove(path)


tenants = Collection("tenants")
users = Collection("users")
reports = Collection("reports")
hazards = Collection("hazards")
risk_assessments = Collection("risk_assessments")
cans = Collection("cans")
caps = Collection("caps")
