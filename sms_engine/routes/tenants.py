from fastapi import APIRouter, Depends
from sms_engine.models import Tenant, User
from sms_engine.database import tenants as tenants_db, users as users_db
from sms_engine.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/v1")


@router.post("/admin/tenants")
def create_tenant(tenant: Tenant, user: CurrentUser = Depends(get_current_user)):
    if not user.is_regulator:
        from fastapi import HTTPException
        raise HTTPException(403, "Regulator access required")
    doc_id = tenants_db.add(tenant.model_dump())
    return {"id": doc_id, "name": tenant.name, "code": tenant.code}


@router.post("/admin/tenants/{tenant_id}/users")
def create_user(tenant_id: str, usr: User, user: CurrentUser = Depends(get_current_user)):
    if not user.is_regulator:
        from fastapi import HTTPException
        raise HTTPException(403, "Regulator access required")
    usr.tenant_id = tenant_id
    doc_id = users_db.add(usr.model_dump())
    return {"id": doc_id, "email": usr.email, "role": usr.role}
