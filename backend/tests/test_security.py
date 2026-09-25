from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    password = "StrongPassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_contains_identity_and_roles() -> None:
    token = create_access_token("user-id", "tenant-id", ["admin"])
    payload = decode_access_token(token)
    assert payload["sub"] == "user-id"
    assert payload["tenant_id"] == "tenant-id"
    assert payload["roles"] == ["admin"]
    assert payload["type"] == "access"
