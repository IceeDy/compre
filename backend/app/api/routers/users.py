from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_roles

router = APIRouter(prefix="/users", tags=["users"])
AdminUser = Annotated[object, Depends(require_roles("admin"))]


@router.get("/me")
def current_user(user: CurrentUser) -> dict:
    return {
        "id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "full_name": user.full_name,
        "roles": [role.name for role in user.roles],
    }


@router.get("/admin-check")
def admin_check(user: AdminUser) -> dict:
    return {"ok": True, "user_id": str(user.id)}
