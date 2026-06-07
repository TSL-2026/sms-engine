"""
Simplified multi-tenant auth middleware.
Uses API key header for simplicity. In production, replace with Firebase Auth / OAuth2.
"""

from fastapi import Request, HTTPException, Depends
from sms_engine.config import settings
from sms_engine.database import users as users_db

AUTHORIZED_API_KEYS = {
    "dev-key-regulator": {"tenant_id": "*", "role": "regulator", "user_id": "dev-regulator"},
    "dev-key-operator": {"tenant_id": "tenant-001", "role": "safety_manager", "user_id": "dev-safety"},
}


class CurrentUser:
    def __init__(self, user_id: str, tenant_id: str, role: str, email: str = ""):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.email = email

    @property
    def is_regulator(self) -> bool:
        return self.role == "regulator"

    def can_access_tenant(self, tenant_id: str) -> bool:
        return self.is_regulator or self.tenant_id == tenant_id


async def get_current_user(request: Request) -> CurrentUser:
    api_key = request.headers.get("X-API-Key", "")
    if api_key in AUTHORIZED_API_KEYS:
        info = AUTHORIZED_API_KEYS[api_key]
        return CurrentUser(
            user_id=info["user_id"],
            tenant_id=info["tenant_id"],
            role=info["role"],
        )

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer dev-token-"):
        parts = auth_header.replace("Bearer ", "").split("-")
        return CurrentUser(
            user_id=auth_header,
            tenant_id=parts[-1] if len(parts) > 1 else "tenant-001",
            role="safety_manager",
        )

    raise HTTPException(status_code=401, detail="Invalid or missing API key")
