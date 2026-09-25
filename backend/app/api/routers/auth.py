from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth import AuthError, authenticate, register_tenant, token_for_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> UserResponse:
    try:
        user = register_tenant(db, **payload.model_dump())
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return UserResponse(
        id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        full_name=user.full_name,
        roles=[role.name for role in user.roles],
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = authenticate(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=token_for_user(user))
