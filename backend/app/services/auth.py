import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User


class AuthError(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_tenant(
    db: Session,
    *,
    tenant_name: str,
    tenant_slug: str,
    full_name: str,
    email: str,
    password: str,
) -> User:
    email = normalize_email(email)
    tenant_slug = tenant_slug.strip().lower()

    if db.scalar(select(Tenant).where(Tenant.slug == tenant_slug)):
        raise AuthError("tenant_slug_already_exists")

    tenant = Tenant(name=tenant_name.strip(), slug=tenant_slug)
    db.add(tenant)
    db.flush()

    role = Role(name="admin", tenant_id=tenant.id)
    user = User(
        tenant_id=tenant.id,
        email=email,
        full_name=full_name.strip(),
        password_hash=hash_password(password),
    )
    user.roles.append(role)
    db.add_all([role, user])
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, *, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user


def token_for_user(user: User) -> str:
    return create_access_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id),
        roles=[role.name for role in user.roles],
    )
