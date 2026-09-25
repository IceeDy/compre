from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    auth,
    commercial,
    finance,
    fulfillment,
    orders,
    supplier_orders,
    supplier_registrations,
    tenants,
    users,
)
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.6.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(tenants.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(commercial.router, prefix="/api/v1")
    app.include_router(finance.router, prefix="/api/v1")
    app.include_router(orders.router, prefix="/api/v1")
    app.include_router(supplier_registrations.router, prefix="/api/v1")
    app.include_router(supplier_orders.router, prefix="/api/v1")
    app.include_router(fulfillment.router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
