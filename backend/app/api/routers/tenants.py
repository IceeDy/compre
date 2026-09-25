from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.schemas.tenant import TenantResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/me", response_model=TenantResponse)
def current_tenant(user: CurrentUser) -> TenantResponse:
    tenant = user.tenant
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
    )
